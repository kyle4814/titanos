def test_data_hash_contract():
    from titanos_stub import execute_data_hash
    assert execute_data_hash(None).status == "REJECT"
    assert execute_data_hash({}).status == "PROPOSED"
