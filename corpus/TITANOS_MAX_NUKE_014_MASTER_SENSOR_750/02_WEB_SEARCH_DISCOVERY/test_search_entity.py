def test_search_entity_contract():
    from titanos_stub import observe_search_entity
    assert observe_search_entity({})["status"] == "OBSERVED"
