def test_sensor_freshness_contract():
    from titanos_stub import observe_sensor_freshness
    assert observe_sensor_freshness({})["status"] == "OBSERVED"
