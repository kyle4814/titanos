def test_sensor_adapter_contract():
    from titanos_stub import observe_sensor_adapter
    assert observe_sensor_adapter({})["status"] == "OBSERVED"
