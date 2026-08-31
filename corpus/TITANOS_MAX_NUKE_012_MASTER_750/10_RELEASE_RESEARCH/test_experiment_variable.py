def test_experiment_variable_contract():
    from titanos_stub import validate_experiment_variable
    assert validate_experiment_variable({})["status"] == "PROPOSED"
