def test_portal_partner_contract():
    from titanos_stub import validate_portal_partner
    assert validate_portal_partner({})["status"] == "PROPOSED"
