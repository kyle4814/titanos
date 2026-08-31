"""Contract tests for brick_adrs.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_brick_adrs_rejects_invalid_input():
    from titanos_stub import execute_brick_adrs
    result = execute_brick_adrs(None)
    assert result.status == "REJECT"

def test_brick_adrs_does_not_claim_implementation():
    from titanos_stub import execute_brick_adrs
    result = execute_brick_adrs({})
    assert result.status == "PROPOSED"
