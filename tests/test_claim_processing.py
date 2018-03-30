from os import environ

import pytest
from electrumx.server.env import Env

from lbryumx.block_processor import claim_id_hash
from lbryumx.coin import LBC
from lbryumx.model import NameClaim, TxClaimOutput, ClaimInfo


@pytest.fixture()
def block_processor(request, tmpdir):
    environ.clear()
    environ['DB_DIRECTORY'] = tmpdir.strpath
    environ['DAEMON_URL'] = ''
    env = Env(LBC)
    return LBC.BLOCK_PROCESSOR(env, None, None)


def test_simple_claim_info_import(block_processor):
    address = 'bTZito1AqWPig64GBioom11mHpoegMfXHx'
    pk_script = LBC.pay_to_address_script(address)
    output = TxClaimOutput(value=10, pk_script=pk_script, claim=NameClaim(name=b'potatoes', value=b'are_nice'))
    height, txid, nout = 42, b'txid', 300
    block_processor.advance_claim_name_transaction(output, height, txid, nout)
    claim_id = claim_id_hash(txid, nout)

    claim_info = block_processor.get_claim_info(claim_id)
    expected_claim_info = ClaimInfo(b'potatoes', b'are_nice', txid, nout, output.value, address, height, cert_id=None)
    assert claim_info.serialized == expected_claim_info.serialized
