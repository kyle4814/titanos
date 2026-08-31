def test_portal_billing_contract():
    from titanos_stub import execute_portal_billing
    assert execute_portal_billing(None).status == "REJECT"
    assert execute_portal_billing({}).status == "PROPOSED"
