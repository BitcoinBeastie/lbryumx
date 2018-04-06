from binascii import unhexlify, hexlify

from electrumx.lib.hash import hex_str_to_hash

from lbryumx.coin import LBC
from lbryumx.model import NameClaim, ClaimUpdate


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
    claims = _filter_tx_output_claims_by_type(block_info, NameClaim)
    assert len(claims) == 1
    claim = claims[0]
    assert claim.name.decode() in block_info['claims']
    assert claim.value == unhexlify(block_info['claims'][claim.name.decode()])


def test_tx_parser_handles_update_claims(block_infos):
    block_info = block_infos['342259']
    claims = _filter_tx_output_claims_by_type(block_info, ClaimUpdate)
    assert len(claims) == 1
    claim = claims[0]
    update_info = block_info['claim_updates'][hexlify(claim.claim_id[::-1]).decode()]
    expected_claim_name, expected_claim_value = update_info[0], unhexlify(update_info[1])
    assert claim.name.decode() == expected_claim_name
    assert claim.value == expected_claim_value


def test_handler_for_claim_script_address_extraction(block_infos):
    block_info = block_infos['342259']
    outputs = _filter_tx_output_by_type(block_info, ClaimUpdate)
    assert LBC.address_from_script(outputs[0].pk_script) == 'bPNQ1zwYeeEFsCBYzQ9F4qLEHv5ZWCf8YB'


def _filter_tx_output_claims_by_type(block_info, claim_type):
    return [output.claim for output in _filter_tx_output_by_type(block_info, claim_type)]


def _filter_tx_output_by_type(block_info, claim_type):
    raw_block = unhexlify(block_info['block'])
    txs = LBC.DESERIALIZER(raw_block, start=LBC.BASIC_HEADER_SIZE).read_tx_block()
    outputs = []
    for tx, _ in txs:
        if tx.has_claims:
            for output in tx.outputs:
                if isinstance(output.claim, claim_type): outputs.append(output)
    return outputs
