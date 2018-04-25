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
    address = 'bTZito1AqWPig64GBioom11mHpoegMfXHx'
    name, value = b'potatoes', b'are_nice'
    output = create_claim_output(address, name, value)
    height, txid, nout = 42, b'txid', 300
    block_processor.advance_claim_name_transaction(output, height, txid, nout)
    claim_id = claim_id_hash(txid, nout)

    claim_info = block_processor.get_claim_info(claim_id)
    expected_claim_info = ClaimInfo(name, value, txid, nout, output.value, address.encode(), height, cert_id=None)
    assert_claim_info_equal(claim_info, expected_claim_info)


def test_signed_claim_info_import(block_processor):
    address = 'bTZito1AqWPig64GBioom11mHpoegMfXHx'
    cert_claim_name = b'@certified-claims'
    cert, privkey = create_cert()
    cert_output = create_claim_output(address, cert_claim_name, cert.serialized)
    height, txid, nout = 42, b'txid', 3
    block_processor.advance_claim_name_transaction(cert_output, height, txid, nout)
    cert_claim_id = claim_id_hash(txid, nout)

    signed_claim_name = b'signed-claim'
    signed_claim_txid = b'signed_txid'
    signed_claim_out = create_claim_output(address, signed_claim_name, claim_data.test_claim_dict,
                                           key=privkey, cert_id=cert_claim_id)
    signed_claim_id = claim_id_hash(signed_claim_txid, nout)
    block_processor.advance_claim_name_transaction(signed_claim_out, height, signed_claim_txid, nout)

    cert_claim_info = block_processor.get_claim_info(cert_claim_id)
    expected_claim_info = ClaimInfo(cert_claim_name, cert.serialized, txid, nout,
                                    cert_output.value, address.encode(), height, cert_id=None)
    assert_claim_info_equal(cert_claim_info, expected_claim_info)

    signed_cert_claim_info = block_processor.get_claim_info(signed_claim_id)
    expected_signed_claim_info = ClaimInfo(signed_claim_name, signed_claim_out.claim.value, signed_claim_txid, nout,
                                           signed_claim_out.value, address.encode(), height,
                                           cert_id=cert_claim_id)
    assert_claim_info_equal(signed_cert_claim_info, expected_signed_claim_info)


def test_claim_sequence_incremented_on_claim_name(block_processor):
    address = 'bTZito1AqWPig64GBioom11mHpoegMfXHx'
    claim_ids = []
    for idx in range(1, 3):
        name, value = b'ordered_claims', "I'm the number {:,d}".format(idx).encode()
        output = create_claim_output(address, name, value)
        height, txid, nout = 42, str(idx).encode(), idx
        block_processor.advance_claim_name_transaction(output, height, txid, nout)
        claim_id = claim_id_hash(txid, nout)
        claim_ids.append(claim_id)

    for idx, claim_id in enumerate(claim_ids, start=1):
        assert block_processor.get_claims_for_name(name)[claim_id] == idx


def test_claim_update_validator(block_processor):
    claim_id = claim_id_hash(b'claimtx', 42)
    prev_hash, prev_idx = b'previous_claim_txid', 42
    input = TxInput(prev_hash, prev_idx, b'script', 1)
    claim = ClaimUpdate(b'name', claim_id, b'new value')
    block_processor.unprocessed_spent_utxo_set.add((prev_hash, prev_idx,))
    assert not block_processor.is_update_valid(claim, [input])

    block_processor.put_claim_info(claim_id, ClaimInfo(b'name', b'value', prev_hash, prev_idx, 20, b'address', 1, None))

    assert block_processor.is_update_valid(claim, [input])



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
