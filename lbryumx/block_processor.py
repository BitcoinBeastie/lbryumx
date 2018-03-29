import hashlib
import struct
import time
from binascii import hexlify
import msgpack

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
        super().open_dbs()

    def flush_utxos(self, utxo_batch):
        # flush claims together with utxos as they are parsed together
        with self.claims_db.write_batch() as claims_batch:
            with self.names_db.write_batch() as names_batch:
                with self.signatures_db.write_batch() as signed_claims_batch:
                    self.flush_claims(claims_batch, names_batch, signed_claims_batch)
        return super().flush_utxos(utxo_batch)

    def flush_claims(self, batch, names_batch, signed_claims_batch):
        flush_start = time.time()
        write_claim, write_name, write_cert = batch.put, names_batch.put, signed_claims_batch.put
        for key, claim in self.claim_cache.items():
            write_claim(key, claim)
        for name, claims in self.claims_for_name_cache.items():
            write_name(name, msgpack.dumps(claims))
        for cert_id, claims in self.claims_signed_by_cert_cache.items():
            write_cert(cert_id, msgpack.dumps(claims))
        if self.claims_db.for_sync:
            self.logger.info('flushed {:,d} blocks with {:,d} claims and {:,d} certificates added'
                             ' in {:.1f}s, committing...'
                             .format(self.height - self.db_height,
                                     len(self.claim_cache), len(self.claims_signed_by_cert_cache),
                                     time.time() - flush_start))
        self.claim_cache = {}
        self.claims_for_name_cache = {}
        self.claims_signed_by_cert_cache = {}

    def assert_flushed(self):
        super().assert_flushed()
        assert not self.claim_cache
        assert not self.claims_for_name_cache
        assert not self.claims_signed_by_cert_cache

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
            parse_lbry_uri(name.decode())  # skip invalid names
            cert_id = smart_decode(value).certificate_id
            if cert_id:
                self.put_claim_id_signed_by_cert_id(cert_id, claim_id)
        except Exception:
            pass
        self.claim_cache[claim_id] = ClaimInfo(name, value, txid, nout, amount, address, height, cert_id).serialized
        self.put_claim_for_name(name, claim_id)

    def get_claims_for_name(self, name):
        if name in self.claims_for_name_cache: return self.claims_for_name_cache[name]
        db_claims = self.names_db.get(name)
        return msgpack.loads(db_claims) if db_claims else {}

    def put_claim_for_name(self, name, claim_id):
        claims = self.get_claims_for_name(name)
        claims[claim_id] = max(claims.values() or [0]) + 1
        self.claims_for_name_cache[name] = claims

    def get_signed_claim_id_by_cert_id(self, cert_id):
        if cert_id in self.claims_signed_by_cert_cache: return self.claims_signed_by_cert_cache[cert_id]
        db_claims = self.signatures_db.get(cert_id)
        return msgpack.loads(db_claims) if db_claims else tuple()

    def put_claim_id_signed_by_cert_id(self, cert_id, claim_id):
        self.claims_signed_by_cert_cache[cert_id] = self.get_signed_claim_id_by_cert_id(cert_id) + (claim_id,)


def claim_id_hash(txid, n):
    # TODO: This should be in lbryschema
    packed = txid + struct.pack('>I', n)
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(packed).digest())
    return hexlify(md.digest()[::-1])
