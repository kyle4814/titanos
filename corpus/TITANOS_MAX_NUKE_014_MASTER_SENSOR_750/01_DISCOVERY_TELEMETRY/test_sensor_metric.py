def test_sensor_metric_contract():
    from titanos_stub import observe_sensor_metric
    assert observe_sensor_metric({})["status"] == "OBSERVED"
