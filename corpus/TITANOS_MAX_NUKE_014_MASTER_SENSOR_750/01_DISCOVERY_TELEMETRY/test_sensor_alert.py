def test_sensor_alert_contract():
    from titanos_stub import observe_sensor_alert
    assert observe_sensor_alert({})["status"] == "OBSERVED"
