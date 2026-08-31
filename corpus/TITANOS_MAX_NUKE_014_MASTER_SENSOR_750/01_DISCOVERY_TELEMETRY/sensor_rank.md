def test_sensor_rank_contract():
    from titanos_stub import observe_sensor_rank
    assert observe_sensor_rank({})["status"] == "OBSERVED"
