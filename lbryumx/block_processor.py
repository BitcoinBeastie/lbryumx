import hashlib
import struct
from binascii import hexlify

from electrumx.server.block_processor import BlockProcessor
from lbryschema.decode import smart_decode
from lbryschema.error import DecodeError
from lbryschema.uri import parse_lbry_uri
from lbryschema.error import URIParseError

from lbryumx.opcodes import NameClaim, ClaimUpdate, ClaimSupport


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
        get_address = self.coin.address_from_script
        height = self.height + 1
        put_claim = self.claim_cache.__setitem__
        claim_name_sequence = self.claim_name_sequence_cache
        for tx, txid in txs:
            if tx.has_claims:
                for index, output in enumerate(tx.outputs):
                    claim = output.claim
                    if isinstance(claim, NameClaim):
                        claim_id = claim_id_hash(txid, index)
                        name = claim.name
                        value = claim.value
                        address = get_address(output.pk_script)
                        cert_id = None
                        try:
                            parse_lbry_uri(claim.name)  # skip invalid names
                            decoded_claim = smart_decode(claim.value)
                            cert_id = decoded_claim.certificate_id
                        except Exception:
                            pass
                        put_claim(claim_id, (name, value, address, height, cert_id))
                        claims_for_name = claim_name_sequence.get(claim.name, {})
                        if not claims_for_name:
                            claims_for_name[claim_id] = 1
                        else:
                            claims_for_name[claim_id] = max(i for i in claims_for_name.values()) + 1
                        claim_name_sequence[claim.name] = claims_for_name
                        # TODO: add cert_id->[signatures,]
        return undo_info


def claim_id_hash(txid, n):
    # TODO: This should be in lbryschema
    packed = txid + struct.pack('>I', n)
    md = hashlib.new('ripemd160')
    md.update(hashlib.sha256(packed).digest())
    return hexlify(md.digest()[::-1])
