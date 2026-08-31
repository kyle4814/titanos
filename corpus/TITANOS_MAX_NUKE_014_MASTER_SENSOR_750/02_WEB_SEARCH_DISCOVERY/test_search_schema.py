def test_search_schema_contract():
    from titanos_stub import observe_search_schema
    assert observe_search_schema({})["status"] == "OBSERVED"
