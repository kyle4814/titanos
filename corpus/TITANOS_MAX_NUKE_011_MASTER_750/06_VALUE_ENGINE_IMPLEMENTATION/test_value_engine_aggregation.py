def test_value_engine_aggregation_contract():
    from titanos_stub import execute_value_engine_aggregation
    assert execute_value_engine_aggregation(None).status == "REJECT"
    assert execute_value_engine_aggregation({}).status == "PROPOSED"
