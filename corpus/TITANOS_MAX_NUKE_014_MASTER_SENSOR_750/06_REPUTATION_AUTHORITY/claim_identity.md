def test_claim_identity_contract():
    from titanos_stub import observe_claim_identity
    assert observe_claim_identity({})["status"] == "OBSERVED"
