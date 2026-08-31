def test_search_result_contract():
    from titanos_stub import observe_search_result
    assert observe_search_result({})["status"] == "OBSERVED"
