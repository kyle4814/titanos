def test_api_provenance_contract():
    from titanos_stub import execute_api_provenance
    assert execute_api_provenance(None).status == "REJECT"
    assert execute_api_provenance({}).status == "PROPOSED"
