import hashlib
import struct
import time
from binascii import hexlify
import msgpack

from electrumx.server.block_processor import BlockProcessor
from lbryschema.decode import smart_decode
from lbryschema.uri import parse_lbry_uri

from lbryumx.model import NameClaim, ClaimInfo, ClaimUpdate


class LBRYBlockProcessor(BlockProcessor):

    def __init__(self, *args, **kwargs):
        self.claim_cache = {}
        self.claims_for_name_cache = {}
        self.claims_signed_by_cert_cache = {}
        self.outpoint_to_claim_id_cache = {}
        self.claims_db = self.names_db = self.signatures_db = self.outpoint_to_claim_id_db = None
        super().__init__(*args, **kwargs)

        # stores deletes not yet flushed to disk
        self.pending_abandons = {}

    def open_dbs(self):
        super().open_dbs()
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
                self.outpoint_to_claim_id_db.close()
            self.claims_db = self.db_class('claims', for_sync)
            self.names_db = self.db_class('names', for_sync)
            self.signatures_db = self.db_class('signatures', for_sync)
            self.outpoint_to_claim_id_db = self.db_class('outpoint_claim_id', for_sync)
            log_reason('opened claim DBs', self.claims_db.for_sync)

    def flush_utxos(self, utxo_batch):
        # flush claims together with utxos as they are parsed together
        with self.claims_db.write_batch() as claims_batch:
            with self.names_db.write_batch() as names_batch:
                with self.signatures_db.write_batch() as signed_claims_batch:
                    with self.outpoint_to_claim_id_db.write_batch() as outpoint_batch:
                        self.flush_claims(claims_batch, names_batch, signed_claims_batch, outpoint_batch)
        return super().flush_utxos(utxo_batch)

    def flush_claims(self, batch, names_batch, signed_claims_batch, outpoint_batch):
        flush_start = time.time()
        write_claim, write_name, write_cert = batch.put, names_batch.put, signed_claims_batch.put
        write_outpoint = outpoint_batch.put
        delete_claim, delete_outpoint, delete_name = batch.delete, outpoint_batch.delete, names_batch.delete
        delete_cert = signed_claims_batch.delete
        for claim_id, outpoints in self.pending_abandons.items():
            claim = self.get_claim_info(claim_id)
            self.remove_claim_for_name(claim.name, claim_id)
            if claim.cert_id:
                self.remove_claim_from_certificate_claims(claim.cert_id, claim_id)
            self.remove_certificate(claim_id)
            if claim_id in self.claim_cache:
                del self.claim_cache[claim_id]
            delete_claim(claim_id)
            for tx_hash, tx_id in outpoints:
                outpoint = tx_hash + struct.pack('>I', tx_id)
                if outpoint in self.outpoint_to_claim_id_cache:
                    del self.outpoint_to_claim_id_cache[outpoint]
                delete_outpoint(outpoint)
        for key, claim in self.claim_cache.items():
            write_claim(key, claim)
        for name, claims in self.claims_for_name_cache.items():
            if not claims:
                delete_name(name)
            else:
                write_name(name, msgpack.dumps(claims))
        for cert_id, claims in self.claims_signed_by_cert_cache.items():
            if not claims:
                delete_cert(cert_id)
            else:
                write_cert(cert_id, msgpack.dumps(claims))
        for key, claim_id in self.outpoint_to_claim_id_cache.items():
            write_outpoint(key, claim_id)
        if self.claims_db.for_sync:
            self.logger.info('flushed {:,d} blocks with {:,d} claims, {:,d} outpoints, {:,d} names '
                             'and {:,d} certificates added while {:,d} were abandoned in {:.1f}s, committing...'
                             .format(self.height - self.db_height,
                                     len(self.claim_cache), len(self.outpoint_to_claim_id_cache),
                                     len(self.claims_for_name_cache),
                                     len(self.claims_signed_by_cert_cache), len(self.pending_abandons),
                                     time.time() - flush_start))
        self.claim_cache = {}
        self.claims_for_name_cache = {}
        self.claims_signed_by_cert_cache = {}
        self.outpoint_to_claim_id_cache = {}
        self.pending_abandons = {}

    def assert_flushed(self):
        super().assert_flushed()
        assert not self.claim_cache
        assert not self.claims_for_name_cache
        assert not self.claims_signed_by_cert_cache
        assert not self.outpoint_to_claim_id_cache
        assert not self.pending_abandons

    def advance_txs(self, txs):
        # TODO: generate claim undo info!
        undo_info = super().advance_txs(txs)
        height = self.height + 1
        for tx, txid in txs:
            if tx.has_claims:
                for index, output in enumerate(tx.outputs):
                    claim = output.claim
                    if isinstance(claim, NameClaim):
                        self.advance_claim_name_transaction(output, height, txid, index)
                    if isinstance(claim, ClaimUpdate):
                        # TODO: updates removes their abandons
                        pass
        return undo_info

    def advance_claim_name_transaction(self, output, height, txid, nout):
        claim_id = claim_id_hash(txid, nout)
        amount = output.value
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
        self.outpoint_to_claim_id_cache[txid + struct.pack('>I', nout)] = claim_id

    def spend_utxo(self, tx_hash, tx_idx):
        # gather pending abandons during the spend of a utxo
        result = super().spend_utxo(tx_hash, tx_idx)
        claim_id = self.get_claim_id_from_outpoint(tx_hash, tx_idx)
        if claim_id:
            self.pending_abandons.setdefault(claim_id, []).append((tx_hash, tx_idx,))
        return result

    def get_claim_id_from_outpoint(self, tx_hash, tx_idx):
        key = tx_hash + struct.pack('>I', tx_idx)
        return self.outpoint_to_claim_id_cache.get(key) or self.outpoint_to_claim_id_db.get(key)

    def get_claims_for_name(self, name):
        if name in self.claims_for_name_cache: return self.claims_for_name_cache[name]
        db_claims = self.names_db.get(name)
        return msgpack.loads(db_claims) if db_claims else {}

    def put_claim_for_name(self, name, claim_id):
        claims = self.get_claims_for_name(name)
        claims[claim_id] = max(claims.values() or [0]) + 1
        self.claims_for_name_cache[name] = claims

    def remove_claim_for_name(self, name, claim_id):
        claims = self.get_claims_for_name(name)
        claim_n = claims.pop(claim_id)
        for claim_id, number in claims.items():
            if number > claim_n:
                claims[claim_id] = number - 1
        self.claims_for_name_cache[name] = claims

    def get_signed_claim_id_by_cert_id(self, cert_id):
        if cert_id in self.claims_signed_by_cert_cache: return self.claims_signed_by_cert_cache[cert_id]
        db_claims = self.signatures_db.get(cert_id)
        return msgpack.loads(db_claims) if db_claims else tuple()

    def put_claim_id_signed_by_cert_id(self, cert_id, claim_id):
        self.claims_signed_by_cert_cache[cert_id] = self.get_signed_claim_id_by_cert_id(cert_id) + (claim_id,)

    def remove_certificate(self, cert_id):
        self.claims_signed_by_cert_cache[cert_id] = tuple()

    def remove_claim_from_certificate_claims(self, cert_id, claim_id):
        certs = self.get_signed_claim_id_by_cert_id(cert_id)
        certs = tuple(filter(lambda claimed_id: claimed_id != claim_id, certs))
        self.claims_signed_by_cert_cache[cert_id] = certs

    def get_claim_info(self, claim_id):
        serialized = self.claim_cache.get(claim_id) or self.claims_db.get(claim_id)
        return ClaimInfo.from_serialized(serialized) if serialized else None



def claim_id_hash(txid, n):
    # TODO: This should be in lbryschema
    packed = txid + struct.pack('>I', n)
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(packed).digest())
    return hexlify(md.digest()[::-1])
