"""Contract tests for brick_inputs.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_brick_inputs_rejects_invalid_input():
    from titanos_stub import execute_brick_inputs
    result = execute_brick_inputs(None)
    assert result.status == "REJECT"

def test_brick_inputs_does_not_claim_implementation():
    from titanos_stub import execute_brick_inputs
    result = execute_brick_inputs({})
    assert result.status == "PROPOSED"
