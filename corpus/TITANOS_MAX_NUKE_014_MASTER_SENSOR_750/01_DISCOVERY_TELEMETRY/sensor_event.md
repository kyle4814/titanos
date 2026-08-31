def test_sensor_event_contract():
    from titanos_stub import observe_sensor_event
    assert observe_sensor_event({})["status"] == "OBSERVED"
