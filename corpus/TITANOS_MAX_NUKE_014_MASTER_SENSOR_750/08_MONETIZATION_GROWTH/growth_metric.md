def test_growth_metric_contract():
    from titanos_stub import observe_growth_metric
    assert observe_growth_metric({})["status"] == "OBSERVED"
