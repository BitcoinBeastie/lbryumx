from binascii import unhexlify
from unittest.mock import MagicMock

import pytest

from .data.regtest_chain import hex_blocks, expected_names, expected_claims
from lbryumx.coin import LBCRegTest


@pytest.mark.asyncio
async def test_simple_claim_backup(block_processor):
    daemon_mock = MagicMock()
    daemon_mock.cached_height.return_value = 0
    block_processor.coin = LBCRegTest
    block_processor.daemon = daemon_mock

    raw_blocks = list(map(unhexlify, hex_blocks))
    blocks = [LBCRegTest.block(raw_block, i) for (i, raw_block) in enumerate(raw_blocks)]
    empty_blocks = raw_blocks[:101]
    first_claim_block = blocks[102]
    await block_processor.check_and_advance_blocks(empty_blocks)
    assert not list(filter(None, map(block_processor.db.get_claims_for_name, expected_names)))

    await block_processor.run_in_thread_with_lock(block_processor.advance_blocks, [first_claim_block])
    # A full flush to disk means a sync is completed
    await block_processor.flush(True)

    # check state with a single claim before backup
    assert len(block_processor.db.get_claims_for_name(expected_names[0])) == 1
    assert not block_processor.db.get_claims_for_name(expected_names[1])
    first_claim_id = list(block_processor.db.get_claims_for_name(expected_names[0]).keys())[0]
    parsed_claim_info = block_processor.db.get_claim_info(first_claim_id)
    assert parsed_claim_info

    await block_processor.flush(True)
    await block_processor.run_in_thread_with_lock(block_processor.backup_blocks, [raw_blocks[102]])

    assert not list(filter(None, map(block_processor.db.get_claims_for_name, expected_names)))
    parsed_claim_info = block_processor.db.get_claim_info(first_claim_id)
    assert not parsed_claim_info


@pytest.mark.asyncio
async def test_claim_update_backup(block_processor):
    # that's trickier as we need to revert to the previous state instead
    daemon_mock = MagicMock()
    daemon_mock.cached_height.return_value = 0
    block_processor.coin = LBCRegTest
    block_processor.daemon = daemon_mock

    raw_blocks = list(map(unhexlify, hex_blocks))
    blocks = [LBCRegTest.block(raw_block, i) for (i, raw_block) in enumerate(raw_blocks)]
    up_to_first_claim_blocks = blocks[:103]
    up_to_first_update_blocks = blocks[103:104]

    await block_processor.run_in_thread_with_lock(block_processor.advance_blocks, up_to_first_claim_blocks)
    await block_processor.flush(True)

    first_claim_id = list(block_processor.db.get_claims_for_name(expected_names[0]).keys())[0]
    original_claim_info = block_processor.db.get_claim_info(first_claim_id)
    assert original_claim_info

    await block_processor.run_in_thread_with_lock(block_processor.advance_blocks, up_to_first_update_blocks)
    await block_processor.flush(True)

    updated_claim_info = block_processor.db.get_claim_info(first_claim_id)
    assert updated_claim_info
    assert updated_claim_info != original_claim_info

    await block_processor.run_in_thread_with_lock(block_processor.backup_blocks, list(reversed(raw_blocks[103:104])))

    backed_up_claim_info = block_processor.db.get_claim_info(first_claim_id)
    assert backed_up_claim_info
    assert original_claim_info == backed_up_claim_info

@pytest.mark.asyncio
async def test_reclaim_abandon_on_backup(block_processor):
    daemon_mock = MagicMock()
    daemon_mock.cached_height.return_value = 0
    block_processor.coin = LBCRegTest
    block_processor.daemon = daemon_mock

    raw_blocks = list(map(unhexlify, hex_blocks))
    blocks = [LBCRegTest.block(raw_block, i) for (i, raw_block) in enumerate(raw_blocks)]

    await block_processor.run_in_thread_with_lock(block_processor.advance_blocks, blocks)
    await block_processor.flush(True)

    # the last block is expected to have no claims (they were claimed, updated then abandoned)
    assert not list(filter(None, map(block_processor.db.get_claims_for_name, expected_names)))

    # get back to where everything existed
    await block_processor.run_in_thread_with_lock(block_processor.backup_blocks, list(reversed(raw_blocks[105:])))

    assert block_processor.db.get_claims_for_name(b'first_claim')
    assert block_processor.db.get_claims_for_name(b'second_claim')
    assert block_processor.db.get_claim_info(unhexlify(expected_claims[expected_names[1]][0])[::-1])
    assert block_processor.db.get_claim_info(unhexlify(expected_claims[expected_names[0]][0])[::-1])
