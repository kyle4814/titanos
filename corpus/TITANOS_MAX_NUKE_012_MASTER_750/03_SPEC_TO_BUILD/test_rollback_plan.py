def test_rollback_plan_contract():
    from titanos_stub import validate_rollback_plan
    assert validate_rollback_plan({})["status"] == "PROPOSED"
