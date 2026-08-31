def test_claim_status_contract():
    from titanos_stub import observe_claim_status
    assert observe_claim_status({})["status"] == "OBSERVED"
