import hashlib
import struct
from binascii import hexlify

from electrumx.server.block_processor import BlockProcessor
from lbryschema.decode import smart_decode
from lbryschema.uri import parse_lbry_uri

from lbryumx.model import NameClaim, ClaimUpdate, ClaimSupport


class LBRYBlockProcessor(BlockProcessor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.claim_cache = {}
        self.claim_name_sequence_cache = {}

    def flush_utxos(self, batch):
        # TODO: flush claim caches
        return super().flush_utxos(batch)

    def advance_txs(self, txs):
        undo_info = super().advance_txs(txs)
        height = self.height + 1
        for tx, txid in txs:
            if tx.has_claims:
                for index, output in enumerate(tx.outputs):
                    claim = output.claim
                    if isinstance(claim, NameClaim):
                        claim_id = claim_id_hash(txid, index)
                        self.advance_claim_name_transaction(output, height, claim_id)
        return undo_info

    def advance_claim_name_transaction(self, output, height, claim_id):
        address = self.coin.address_from_script(output.pk_script)
        name, value, cert_id = output.claim.name, output.claim.value, None
        try:
            parse_lbry_uri(name)  # skip invalid names
            cert_id = smart_decode(value).certificate_id
        except Exception:
            pass
        self.claim_cache[claim_id] = (name, value, address, height, cert_id,)

        claims_for_name = self.claim_name_sequence_cache.get(name, {})
        if not claims_for_name:
            claims_for_name[claim_id] = 1
        else:
            claims_for_name[claim_id] = max(i for i in claims_for_name.values()) + 1
        self.claim_name_sequence_cache[name] = claims_for_name
        # TODO: add cert_id->[signatures,]


def claim_id_hash(txid, n):
    # TODO: This should be in lbryschema
    packed = txid + struct.pack('>I', n)
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(packed).digest())
    return hexlify(md.digest()[::-1])
