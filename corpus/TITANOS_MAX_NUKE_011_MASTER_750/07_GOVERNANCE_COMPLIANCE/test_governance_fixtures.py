def test_governance_fixtures_contract():
    from titanos_stub import execute_governance_fixtures
    assert execute_governance_fixtures(None).status == "REJECT"
    assert execute_governance_fixtures({}).status == "PROPOSED"
