"""Contract tests for brick_usage.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_brick_usage_rejects_invalid_input():
    from titanos_stub import execute_brick_usage
    result = execute_brick_usage(None)
    assert result.status == "REJECT"

def test_brick_usage_does_not_claim_implementation():
    from titanos_stub import execute_brick_usage
    result = execute_brick_usage({})
    assert result.status == "PROPOSED"
