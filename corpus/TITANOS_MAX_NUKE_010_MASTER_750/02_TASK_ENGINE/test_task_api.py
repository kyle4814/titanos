"""Contract tests for task_api.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_task_api_rejects_invalid_input():
    from titanos_stub import execute_task_api
    result = execute_task_api(None)
    assert result.status == "REJECT"

def test_task_api_does_not_claim_implementation():
    from titanos_stub import execute_task_api
    result = execute_task_api({})
    assert result.status == "PROPOSED"
