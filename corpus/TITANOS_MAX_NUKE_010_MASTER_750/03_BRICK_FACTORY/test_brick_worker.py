"""Contract tests for brick_worker.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_brick_worker_rejects_invalid_input():
    from titanos_stub import execute_brick_worker
    result = execute_brick_worker(None)
    assert result.status == "REJECT"

def test_brick_worker_does_not_claim_implementation():
    from titanos_stub import execute_brick_worker
    result = execute_brick_worker({})
    assert result.status == "PROPOSED"
