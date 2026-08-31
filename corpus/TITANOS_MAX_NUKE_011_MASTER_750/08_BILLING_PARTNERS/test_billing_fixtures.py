def test_billing_fixtures_contract():
    from titanos_stub import execute_billing_fixtures
    assert execute_billing_fixtures(None).status == "REJECT"
    assert execute_billing_fixtures({}).status == "PROPOSED"
