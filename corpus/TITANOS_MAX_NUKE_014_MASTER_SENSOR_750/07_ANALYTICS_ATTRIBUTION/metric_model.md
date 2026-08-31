def test_metric_model_contract():
    from titanos_stub import observe_metric_model
    assert observe_metric_model({})["status"] == "OBSERVED"
