def test_data_policy_contract():
    from titanos_stub import validate_data_policy
    assert validate_data_policy({})["status"] == "PROPOSED"
