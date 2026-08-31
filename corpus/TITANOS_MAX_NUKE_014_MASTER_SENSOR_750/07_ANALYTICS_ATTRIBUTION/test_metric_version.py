def test_metric_version_contract():
    from titanos_stub import observe_metric_version
    assert observe_metric_version({})["status"] == "OBSERVED"
