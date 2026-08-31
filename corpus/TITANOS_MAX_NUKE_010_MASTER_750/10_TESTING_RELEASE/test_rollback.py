"""Contract tests for rollback.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_rollback_rejects_invalid_input():
    from titanos_stub import execute_rollback
    result = execute_rollback(None)
    assert result.status == "REJECT"

def test_rollback_does_not_claim_implementation():
    from titanos_stub import execute_rollback
    result = execute_rollback({})
    assert result.status == "PROPOSED"
