def test_data_freshness_contract():
    from titanos_stub import execute_data_freshness
    assert execute_data_freshness(None).status == "REJECT"
    assert execute_data_freshness({}).status == "PROPOSED"
