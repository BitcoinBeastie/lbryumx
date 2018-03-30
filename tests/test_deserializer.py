import json
import os
from binascii import unhexlify

import pytest
from electrumx.lib.hash import hex_str_to_hash

from lbryumx.coin import LBC
from lbryumx.model import NameClaim, TxClaimOutput
from lbryumx.tx import LBRYDeserializer


@pytest.fixture('module')
def block_info():
    block_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'block_342930.json')
    with open(block_file_path, 'r') as block_file:
        return json.loads(block_file.read())

def test_block(block_info):
    # From electrumx test_block
    coin = LBC

    raw_block = unhexlify(block_info['block'])
    block = coin.block(raw_block, block_info['height'])

    assert coin.header_hash(block.header) == hex_str_to_hash(block_info['hash'])
    assert (coin.header_prevhash(block.header)
            == hex_str_to_hash(block_info['previousblockhash']))
    for n, (tx, txid) in enumerate(block.transactions):
        assert txid == hex_str_to_hash(block_info['tx'][n])

def test_tx_parser_handles_name_claims(block_info):
    raw_block = unhexlify(block_info['block'])
    txs = LBC.DESERIALIZER(raw_block, start=LBC.BASIC_HEADER_SIZE).read_tx_block()
    claim = None
    for tx, _ in txs:
        for output in tx.outputs:
            claim = output.claim if output.claim else claim
    assert claim
    assert claim.name.decode() in block_info['claims']
    assert claim.value == unhexlify(block_info['claims'][claim.name.decode()])
