def test_portal_contracts_contract():
    from titanos_stub import execute_portal_contracts
    assert execute_portal_contracts(None).status == "REJECT"
    assert execute_portal_contracts({}).status == "PROPOSED"
