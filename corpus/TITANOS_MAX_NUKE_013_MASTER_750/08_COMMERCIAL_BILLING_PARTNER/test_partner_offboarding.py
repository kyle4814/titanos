def test_partner_offboarding_contract():
    from titanos_stub import validate_partner_offboarding
    assert validate_partner_offboarding({})["status"] == "PROPOSED"
