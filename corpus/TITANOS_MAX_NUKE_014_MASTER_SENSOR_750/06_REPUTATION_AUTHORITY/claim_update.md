def test_claim_update_contract():
    from titanos_stub import observe_claim_update
    assert observe_claim_update({})["status"] == "OBSERVED"
