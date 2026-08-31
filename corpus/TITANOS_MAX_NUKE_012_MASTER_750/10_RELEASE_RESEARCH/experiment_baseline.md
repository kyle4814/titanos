def test_experiment_baseline_contract():
    from titanos_stub import validate_experiment_baseline
    assert validate_experiment_baseline({})["status"] == "PROPOSED"
