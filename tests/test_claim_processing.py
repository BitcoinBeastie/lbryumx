from hashlib import sha256
from random import getrandbits

from electrumx.lib.hash import hash_to_str
from electrumx.lib.tx import TxInput
from lbryschema.decode import smart_decode
from lbryschema.schema import SECP256k1
from lbryschema.claim import ClaimDict
from lbryschema.signer import get_signer

from lbryumx.block_processor import claim_id_hash
from lbryumx.coin import LBC
from lbryumx.model import NameClaim, TxClaimOutput, ClaimInfo, ClaimUpdate, ClaimSupport

from .data import claim_data


def test_simple_claim_info_import(block_processor):
    claim_id, expected_claim_info = make_claim(block_processor)

    claim_info = block_processor.get_claim_info(claim_id)
    assert_claim_info_equal(claim_info, expected_claim_info)


def test_signed_claim_info_import(block_processor):
    cert_claim_name = b'@certified-claims'
    cert, privkey = create_cert()
    cert_claim_id, expected_claim_info = make_claim(block_processor, cert_claim_name, cert.serialized)

    signed_claim_name = b'signed-claim'
    value = ClaimDict.load_dict(claim_data.test_claim_dict).serialized
    signed_claim_id, expected_signed_claim_info = make_claim(block_processor, signed_claim_name, value, privkey, cert_claim_id)

    cert_claim_info = block_processor.get_claim_info(cert_claim_id)
    assert_claim_info_equal(cert_claim_info, expected_claim_info)

    signed_cert_claim_info = block_processor.get_claim_info(signed_claim_id)
    assert_claim_info_equal(signed_cert_claim_info, expected_signed_claim_info)


def test_claim_sequence_incremented_on_claim_name(block_processor):
    claim_ids = []
    for idx in range(1, 3):
        claim_id, _ = make_claim(block_processor, name=b'ordered')
        claim_ids.append(claim_id)

    for idx, claim_id in enumerate(claim_ids, start=1):
        assert block_processor.get_claims_for_name(b'ordered')[claim_id] == idx


def test_claim_update_validator(block_processor):
    claim_id = claim_id_hash(b'claimtx', 42)
    prev_hash, prev_idx = b'previous_claim_txid', 42
    input = TxInput(prev_hash, prev_idx, b'script', 1)
    claim = ClaimUpdate(b'name', claim_id, b'new value')
    block_processor.unprocessed_spent_utxo_set.add((prev_hash, prev_idx,))
    assert not block_processor.is_update_valid(claim, [input])

    block_processor.put_claim_info(claim_id, ClaimInfo(b'name', b'value', prev_hash, prev_idx, 20, b'address', 1, None))

    assert block_processor.is_update_valid(claim, [input])


def make_claim(block_processor, name=None, value=None, key=None, cert_id=None):
    address = 'bTZito1AqWPig64GBioom11mHpoegMfXHx'
    name, value = name or b'potatoes', value or b'are_nice'
    output = create_claim_output(address, name, value, key, cert_id)
    height, txid, nout = getrandbits(8), bytes(getrandbits(8) for _ in range(32)), getrandbits(8)
    block_processor.advance_claim_name_transaction(output, height, txid, nout)
    return claim_id_hash(txid, nout), ClaimInfo(name, output.claim.value, txid,
                                                nout, output.value, address.encode(), height, cert_id)


def create_cert():
    private_key = get_signer(SECP256k1).generate().private_key.to_pem()
    certificate = ClaimDict.generate_certificate(private_key, curve=SECP256k1)
    return certificate, private_key


def sign_claim(private_key, raw_claim, address, claim_id):
    claim = smart_decode(raw_claim)
    return claim.sign(private_key, address, hash_to_str(claim_id), curve=SECP256k1)


def create_claim_output(address, name, value, key=None, cert_id=None):
    if key and cert_id:
        value = sign_claim(key, value, address, cert_id).serialized
    pk_script = LBC.pay_to_address_script(address)
    return TxClaimOutput(value=10, pk_script=pk_script, claim=NameClaim(name=name, value=value))


def assert_claim_info_equal(claim1, claim2):
    # helps printing what's different
    for idx, value in enumerate(claim1):
        assert value == claim2[idx]
