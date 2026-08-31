def test_memory_store_contract():
    from titanos_stub import execute_memory_store
    assert execute_memory_store(None).status == "REJECT"
    assert execute_memory_store({}).status == "PROPOSED"
