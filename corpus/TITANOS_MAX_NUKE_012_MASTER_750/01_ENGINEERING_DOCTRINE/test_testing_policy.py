def test_testing_policy_contract():
    from titanos_stub import validate_testing_policy
    assert validate_testing_policy({})["status"] == "PROPOSED"
