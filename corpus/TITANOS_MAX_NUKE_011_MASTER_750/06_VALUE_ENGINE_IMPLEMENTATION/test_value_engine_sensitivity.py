def test_value_engine_sensitivity_contract():
    from titanos_stub import execute_value_engine_sensitivity
    assert execute_value_engine_sensitivity(None).status == "REJECT"
    assert execute_value_engine_sensitivity({}).status == "PROPOSED"
