def test_data_store_contract():
    from titanos_stub import execute_data_store
    assert execute_data_store(None).status == "REJECT"
    assert execute_data_store({}).status == "PROPOSED"
