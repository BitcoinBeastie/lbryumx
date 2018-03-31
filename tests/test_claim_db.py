

def test_claim_sequence_remove_reorders(block_processor):
    name, db = b'name', block_processor
    db.put_claim_for_name(name, 'id1')
    db.put_claim_for_name(name, 'id2')
    db.put_claim_for_name(name, 'id3')
    db.remove_claim_for_name(name, 'id2')

    assert db.get_claims_for_name(name) == {'id1': 1, 'id3': 2}
