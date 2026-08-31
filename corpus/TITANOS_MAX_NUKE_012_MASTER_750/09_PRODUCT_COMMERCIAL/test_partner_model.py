def test_partner_model_contract():
    from titanos_stub import validate_partner_model
    assert validate_partner_model({})["status"] == "PROPOSED"
