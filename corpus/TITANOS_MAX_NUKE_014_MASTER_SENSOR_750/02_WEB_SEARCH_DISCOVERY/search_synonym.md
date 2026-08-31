def test_search_synonym_contract():
    from titanos_stub import observe_search_synonym
    assert observe_search_synonym({})["status"] == "OBSERVED"
