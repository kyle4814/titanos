def test_partner_model_contract():
    from titanos_stub import observe_partner_model
    assert observe_partner_model({})["status"] == "OBSERVED"
