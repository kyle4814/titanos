def test_attribution_window_contract():
    from titanos_stub import observe_attribution_window
    assert observe_attribution_window({})["status"] == "OBSERVED"
