def test_task_quota_contract():
    from titanos_stub import validate_task_quota
    assert validate_task_quota({})["status"] == "PROPOSED"
