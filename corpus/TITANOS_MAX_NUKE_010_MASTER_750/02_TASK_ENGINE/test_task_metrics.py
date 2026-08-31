"""Contract tests for task_metrics.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_task_metrics_rejects_invalid_input():
    from titanos_stub import execute_task_metrics
    result = execute_task_metrics(None)
    assert result.status == "REJECT"

def test_task_metrics_does_not_claim_implementation():
    from titanos_stub import execute_task_metrics
    result = execute_task_metrics({})
    assert result.status == "PROPOSED"
