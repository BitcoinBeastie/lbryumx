from os import environ

import pytest
from lbryschema.decode import smart_decode
from lbryschema.schema import SECP256k1
from electrumx.server.env import Env
from lbryschema.claim import ClaimDict
from lbryschema.signer import get_signer

from lbryumx.block_processor import claim_id_hash
from lbryumx.coin import LBC
from lbryumx.model import NameClaim, TxClaimOutput, ClaimInfo

from .data import claim_data


@pytest.fixture(scope="session")
def block_processor(tmpdir_factory):
    environ.clear()
    environ['DB_DIRECTORY'] = tmpdir_factory.mktemp('bp', numbered=True).strpath
    environ['DAEMON_URL'] = ''
    env = Env(LBC)
    return LBC.BLOCK_PROCESSOR(env, None, None)


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
                                           sign=(cert, privkey), cert_id=cert_claim_id)
    signed_claim_id = claim_id_hash(signed_claim_txid, nout)
    block_processor.advance_claim_name_transaction(signed_claim_out, height, signed_claim_txid, nout)

    cert_claim_info = block_processor.get_claim_info(cert_claim_id)
    expected_claim_info = ClaimInfo(cert_claim_name, cert.serialized, txid, nout,
                                    cert_output.value, address.encode(), height, cert_id=None)
    assert_claim_info_equal(cert_claim_info, expected_claim_info)

    signed_cert_claim_info = block_processor.get_claim_info(signed_claim_id)
    expected_signed_claim_info = ClaimInfo(signed_claim_name, signed_claim_out.claim.value, signed_claim_txid, nout,
                                           signed_claim_out.value, address.encode(), height, cert_id=cert_claim_id)
    assert_claim_info_equal(signed_cert_claim_info, expected_signed_claim_info)


def create_cert():
    private_key = get_signer(SECP256k1).generate().private_key.to_pem()
    certificate = ClaimDict.generate_certificate(private_key, curve=SECP256k1)
    return certificate, private_key


def sign_claim(cert_claim, private_key, raw_claim, address, claim_id):
    claim = smart_decode(raw_claim)
    return claim.sign(private_key, address, claim_id, curve=SECP256k1)


def create_claim_output(address, name, value, sign=None, cert_id=None):
    if sign and cert_id:
        value = sign_claim(sign[0], sign[1], value, address, cert_id).serialized
    pk_script = LBC.pay_to_address_script(address)
    return TxClaimOutput(value=10, pk_script=pk_script, claim=NameClaim(name=name, value=value))


def assert_claim_info_equal(claim1, claim2):
    # helps printing what's different
    for idx, value in enumerate(claim1):
        assert value == claim2[idx]
