def test_metric_freshness_contract():
    from titanos_stub import observe_metric_freshness
    assert observe_metric_freshness({})["status"] == "OBSERVED"
