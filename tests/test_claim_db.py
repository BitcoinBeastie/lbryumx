import json
from binascii import hexlify

from electrumx.lib.hash import hash_to_str

from lbryumx.model import ClaimInfo


def test_claim_sequence_remove_reorders(block_processor):
    name, db = b'name', block_processor
    db.put_claim_for_name(name, b'id1')
    db.put_claim_for_name(name, b'id2')
    db.put_claim_for_name(name, b'id3')
    db.remove_claim_for_name(name, b'id2')

    assert db.get_claims_for_name(name) == {b'id1': 1, b'id3': 2}


def test_cert_to_claims_storage(block_processor):
    db = block_processor
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id1')
    db.put_claim_id_signed_by_cert_id(b'certificate_id2', b'claim_id2')
    assert db.get_signed_claim_ids_by_cert_id(b'certificate_id') == [b'claim_id1']


def test_cert_to_claims_storage_removal_of_certificate(block_processor):
    db = block_processor
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id1')
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id2')
    db.remove_certificate(b'certificate_id')
    assert db.get_signed_claim_ids_by_cert_id(b'certificate_id') == list()


def test_cert_to_claims_storage_removal_of_claim_id(block_processor):
    db = block_processor
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id1')
    db.put_claim_id_signed_by_cert_id(b'certificate_id', b'claim_id2')
    db.remove_claim_from_certificate_claims(b'certificate_id', b'claim_id1')
    assert db.get_signed_claim_ids_by_cert_id(b'certificate_id') == [b'claim_id2']


def test_claim_id_outpoint_retrieval(block_processor):
    db = block_processor
    db.put_claim_id_for_outpoint(b'txid bytes', tx_idx=2, claim_id=b'400cafe800')
    assert db.get_claim_id_from_outpoint(b'txid bytes', tx_idx=2) == b'400cafe800'


def test_pending_abandons_trigger(block_processor):
    block_processor.abandon_spent(b'inexistent_tx', 2)
    assert not block_processor.pending_abandons
    block_processor.put_claim_id_for_outpoint(b'existing_tx', tx_idx=4, claim_id=b'1337')
    block_processor.abandon_spent(b'existing_tx', 4)
    assert b'1337' in block_processor.pending_abandons
