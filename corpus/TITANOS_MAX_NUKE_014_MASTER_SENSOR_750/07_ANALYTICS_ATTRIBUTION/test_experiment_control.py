def test_experiment_control_contract():
    from titanos_stub import observe_experiment_control
    assert observe_experiment_control({})["status"] == "OBSERVED"
