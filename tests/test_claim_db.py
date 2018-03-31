

def test_claim_sequence_remove_reorders(block_processor):
    name, db = b'name', block_processor
    db.put_claim_for_name(name, 'id1')
    db.put_claim_for_name(name, 'id2')
    db.put_claim_for_name(name, 'id3')
    db.remove_claim_for_name(name, 'id2')

    assert db.get_claims_for_name(name) == {'id1': 1, 'id3': 2}


def test_cert_to_claims_storage(block_processor):
    db = block_processor
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id1')
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id2')
    assert db.get_signed_claim_id_by_cert_id(b'certificate_id') == (b'claim_id1', b'claim_id2')