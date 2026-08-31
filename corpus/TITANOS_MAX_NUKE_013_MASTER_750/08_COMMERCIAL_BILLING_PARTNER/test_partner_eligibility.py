def test_partner_eligibility_contract():
    from titanos_stub import validate_partner_eligibility
    assert validate_partner_eligibility({})["status"] == "PROPOSED"
