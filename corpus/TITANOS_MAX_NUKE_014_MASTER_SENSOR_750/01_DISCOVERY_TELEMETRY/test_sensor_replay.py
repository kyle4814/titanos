def test_sensor_replay_contract():
    from titanos_stub import observe_sensor_replay
    assert observe_sensor_replay({})["status"] == "OBSERVED"
