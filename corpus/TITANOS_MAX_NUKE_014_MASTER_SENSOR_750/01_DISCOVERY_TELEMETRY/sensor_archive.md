def test_sensor_archive_contract():
    from titanos_stub import observe_sensor_archive
    assert observe_sensor_archive({})["status"] == "OBSERVED"
