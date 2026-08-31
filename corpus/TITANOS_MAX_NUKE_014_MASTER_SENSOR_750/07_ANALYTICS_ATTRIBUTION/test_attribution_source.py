def test_attribution_source_contract():
    from titanos_stub import observe_attribution_source
    assert observe_attribution_source({})["status"] == "OBSERVED"
