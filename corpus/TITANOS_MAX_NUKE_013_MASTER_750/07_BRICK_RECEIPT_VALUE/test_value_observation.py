def test_value_observation_contract():
    from titanos_stub import validate_value_observation
    assert validate_value_observation({})["status"] == "PROPOSED"
