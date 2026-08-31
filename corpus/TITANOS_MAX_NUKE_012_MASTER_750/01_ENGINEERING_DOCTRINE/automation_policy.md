def test_automation_policy_contract():
    from titanos_stub import validate_automation_policy
    assert validate_automation_policy({})["status"] == "PROPOSED"
