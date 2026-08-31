def test_search_failure_contract():
    from titanos_stub import observe_search_failure
    assert observe_search_failure({})["status"] == "OBSERVED"
