def test_commit_policy_contract():
    from titanos_stub import validate_commit_policy
    assert validate_commit_policy({})["status"] == "PROPOSED"
