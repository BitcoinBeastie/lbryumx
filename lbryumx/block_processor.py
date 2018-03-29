import hashlib
import struct
import time
from binascii import hexlify

from electrumx.server.block_processor import BlockProcessor
from lbryschema.decode import smart_decode
from lbryschema.uri import parse_lbry_uri

from lbryumx.model import NameClaim, ClaimInfo


class LBRYBlockProcessor(BlockProcessor):

    def __init__(self, *args, **kwargs):
        self.claim_cache = {}
        self.claims_for_name_cache = {}
        self.claims_signed_by_cert_cache = {}
        self.claims_db = self.names_db = self.signatures_db = None
        super().__init__(*args, **kwargs)

    def open_dbs(self):
        return super().open_dbs()
        def log_reason(message, is_for_sync):
            reason = 'sync' if is_for_sync else 'serving'
            self.logger.info('{} for {}'.format(message, reason))

        for for_sync in [False, True]:
            if self.claims_db:
                if self.claims_db.for_sync == for_sync:
                    return
                log_reason('closing claim DBs to re-open', for_sync)
                self.claims_db.close()
                self.names_db.close()
                self.signatures_db.close()
            self.claims_db = self.db_class('claims', for_sync)
            self.names_db = self.db_class('names', for_sync)
            self.signatures_db = self.db_class('signatures', for_sync)
            log_reason('opened claim DBs', self.claims_db.for_sync)

    def flush_utxos(self, utxo_batch):
        # flush claims together with utxos as they are parsed together
        # TODO: flush names and signatures caches
        with self.utxo_db.write_batch() as claims_batch:
            self.flush_claims(claims_batch)
        return super().flush_utxos(utxo_batch)

    def flush_claims(self, batch):
        flush_start = time.time()
        write = batch.put
        for key, claim in self.claim_cache.items():
            write(key, claim)
        if self.utxo_db.for_sync:
            self.logger.info('flushed {:,d} blocks with {:,d} claims '
                             'added, {:,d} deleted in {:.1f}s, committing...'
                             .format(self.height - self.db_height,
                                     len(self.claim_cache), 0,
                                     time.time() - flush_start))
        self.claim_cache = {}

    def assert_flushed(self):
        super().assert_flushed()
        assert not self.claim_cache

    def advance_txs(self, txs):
        # TODO: generate claim undo info!
        undo_info = super().advance_txs(txs)
        height = self.height + 1
        for tx, txid in txs:
            if tx.has_claims:
                for index, output in enumerate(tx.outputs):
                    claim = output.claim
                    if isinstance(claim, NameClaim):
                        claim_id = claim_id_hash(txid, index)
                        self.advance_claim_name_transaction(output, height, claim_id, txid, index, output.value)
        return undo_info

    def advance_claim_name_transaction(self, output, height, claim_id, txid, nout, amount):
        address = self.coin.address_from_script(output.pk_script)
        name, value, cert_id = output.claim.name, output.claim.value, None
        try:
            parse_lbry_uri(name)  # skip invalid names
            cert_id = smart_decode(value).certificate_id
            self.claims_signed_by_cert_cache.setdefault(cert_id, []).append(claim_id)
        except Exception:
            pass
        self.claim_cache[claim_id] = ClaimInfo(name, value, txid, nout, amount, address, height, cert_id).serialized

        claims_for_name = self.claims_for_name_cache.get(name, {}).values()
        self.claims_for_name_cache.setdefault(name, {})[claim_id] = max(claims_for_name or [0]) + 1


def claim_id_hash(txid, n):
    # TODO: This should be in lbryschema
    packed = txid + struct.pack('>I', n)
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(packed).digest())
    return hexlify(md.digest()[::-1])
