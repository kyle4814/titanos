def test_partner_contract_contract():
    from titanos_stub import execute_partner_contract
    assert execute_partner_contract(None).status == "REJECT"
    assert execute_partner_contract({}).status == "PROPOSED"
