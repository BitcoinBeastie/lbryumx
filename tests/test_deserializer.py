import json
import os
from binascii import unhexlify, hexlify

import pytest
from electrumx.lib.hash import hex_str_to_hash

from lbryumx.coin import LBC
from lbryumx.model import NameClaim, ClaimUpdate


@pytest.fixture('module')
def block_infos():
    block_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    blocks = {}
    for block_file_name in os.listdir(block_data_path):
        number = block_file_name.split('_')[1].replace('.json', '')
        block_file_path = os.path.join(block_data_path, block_file_name)
        with open(block_file_path, 'r') as block_file:
            blocks[number] = json.loads(block_file.read())
    return blocks


def test_block(block_infos):
    # From electrumx test_block 342930
    coin = LBC
    block_info = block_infos['342930']

    raw_block = unhexlify(block_info['block'])
    block = coin.block(raw_block, block_info['height'])

    assert coin.header_hash(block.header) == hex_str_to_hash(block_info['hash'])
    assert (coin.header_prevhash(block.header)
            == hex_str_to_hash(block_info['previousblockhash']))
    for n, (tx, txid) in enumerate(block.transactions):
        assert txid == hex_str_to_hash(block_info['tx'][n])


def test_tx_parser_handles_name_claims(block_infos):
    block_info = block_infos['342930']
    raw_block = unhexlify(block_info['block'])
    txs = LBC.DESERIALIZER(raw_block, start=LBC.BASIC_HEADER_SIZE).read_tx_block()
    for tx, _ in txs:
        if tx.has_claims:
            for output in tx.outputs:
                claim = output.claim if output.claim else claim
    assert claim and isinstance(claim, NameClaim)
    assert claim.name.decode() in block_info['claims']
    assert claim.value == unhexlify(block_info['claims'][claim.name.decode()])


def test_tx_parser_handles_update_claims(block_infos):
    block_info = block_infos['342259']
    raw_block = unhexlify(block_info['block'])
    txs = LBC.DESERIALIZER(raw_block, start=LBC.BASIC_HEADER_SIZE).read_tx_block()
    for tx, _ in txs:
        if tx.has_claims:
            for output in tx.outputs:
                claim = output.claim if output.claim else claim
    assert claim and isinstance(claim, ClaimUpdate)
    update_info = block_info['claim_updates'][hexlify(claim.claim_id[::-1]).decode()]
    expected_claim_name, expected_claim_value = update_info[0], unhexlify(update_info[1])
    assert claim.name.decode() == expected_claim_name
    assert claim.value == expected_claim_value
