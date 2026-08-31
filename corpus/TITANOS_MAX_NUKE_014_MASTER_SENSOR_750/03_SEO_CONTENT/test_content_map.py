def test_content_map_contract():
    from titanos_stub import observe_content_map
    assert observe_content_map({})["status"] == "OBSERVED"
