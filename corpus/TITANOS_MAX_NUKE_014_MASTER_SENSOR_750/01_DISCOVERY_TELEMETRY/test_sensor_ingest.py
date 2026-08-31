def test_sensor_ingest_contract():
    from titanos_stub import observe_sensor_ingest
    assert observe_sensor_ingest({})["status"] == "OBSERVED"
