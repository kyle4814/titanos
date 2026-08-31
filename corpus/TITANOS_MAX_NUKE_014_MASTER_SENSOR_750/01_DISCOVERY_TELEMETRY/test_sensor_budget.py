def test_sensor_budget_contract():
    from titanos_stub import observe_sensor_budget
    assert observe_sensor_budget({})["status"] == "OBSERVED"
