def test_memory_relevance_contract():
    from titanos_stub import execute_memory_relevance
    assert execute_memory_relevance(None).status == "REJECT"
    assert execute_memory_relevance({}).status == "PROPOSED"
