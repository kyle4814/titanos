def test_value_engine_partner_contract():
    from titanos_stub import execute_value_engine_partner
    assert execute_value_engine_partner(None).status == "REJECT"
    assert execute_value_engine_partner({}).status == "PROPOSED"
