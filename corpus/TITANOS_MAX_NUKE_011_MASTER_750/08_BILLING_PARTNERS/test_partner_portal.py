def test_partner_portal_contract():
    from titanos_stub import execute_partner_portal
    assert execute_partner_portal(None).status == "REJECT"
    assert execute_partner_portal({}).status == "PROPOSED"
