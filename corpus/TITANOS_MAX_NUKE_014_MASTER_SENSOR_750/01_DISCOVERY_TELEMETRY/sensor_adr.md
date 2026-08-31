def test_sensor_adr_contract():
    from titanos_stub import observe_sensor_adr
    assert observe_sensor_adr({})["status"] == "OBSERVED"
