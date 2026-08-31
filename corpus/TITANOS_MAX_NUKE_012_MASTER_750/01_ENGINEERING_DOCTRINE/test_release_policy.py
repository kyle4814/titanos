def test_release_policy_contract():
    from titanos_stub import validate_release_policy
    assert validate_release_policy({})["status"] == "PROPOSED"
