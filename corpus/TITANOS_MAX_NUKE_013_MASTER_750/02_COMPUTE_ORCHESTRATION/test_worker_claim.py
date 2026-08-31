def test_worker_claim_contract():
    from titanos_stub import validate_worker_claim
    assert validate_worker_claim({})["status"] == "PROPOSED"
