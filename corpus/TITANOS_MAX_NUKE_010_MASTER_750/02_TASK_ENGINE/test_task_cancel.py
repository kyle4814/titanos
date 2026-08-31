"""Contract tests for task_cancel.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_task_cancel_rejects_invalid_input():
    from titanos_stub import execute_task_cancel
    result = execute_task_cancel(None)
    assert result.status == "REJECT"

def test_task_cancel_does_not_claim_implementation():
    from titanos_stub import execute_task_cancel
    result = execute_task_cancel({})
    assert result.status == "PROPOSED"
