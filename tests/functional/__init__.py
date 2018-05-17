import pytest


@pytest.mark.asyncio
async def test_command(regtest_session):
    result = await regtest_session.claimtrie_getclaimsforname('@FreeKeene')
    assert result['claims'] == 1, result

