def test_portal_partner_onboarding_contract():
    from titanos_stub import execute_portal_partner_onboarding
    assert execute_portal_partner_onboarding(None).status == "REJECT"
    assert execute_portal_partner_onboarding({}).status == "PROPOSED"
