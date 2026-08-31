def test_sensor_rate_limit_contract():
    from titanos_stub import observe_sensor_rate_limit
    assert observe_sensor_rate_limit({})["status"] == "OBSERVED"
