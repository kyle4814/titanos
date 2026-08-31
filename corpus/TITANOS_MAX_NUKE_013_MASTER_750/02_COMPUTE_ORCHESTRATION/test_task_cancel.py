def test_task_cancel_contract():
    from titanos_stub import validate_task_cancel
    assert validate_task_cancel({})["status"] == "PROPOSED"
