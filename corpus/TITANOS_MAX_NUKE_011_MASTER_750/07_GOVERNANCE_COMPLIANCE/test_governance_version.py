def test_governance_version_contract():
    from titanos_stub import execute_governance_version
    assert execute_governance_version(None).status == "REJECT"
    assert execute_governance_version({}).status == "PROPOSED"
