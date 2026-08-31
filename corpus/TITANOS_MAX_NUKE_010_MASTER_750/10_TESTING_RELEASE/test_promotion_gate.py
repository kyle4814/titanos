"""Contract tests for promotion_gate.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_promotion_gate_rejects_invalid_input():
    from titanos_stub import execute_promotion_gate
    result = execute_promotion_gate(None)
    assert result.status == "REJECT"

def test_promotion_gate_does_not_claim_implementation():
    from titanos_stub import execute_promotion_gate
    result = execute_promotion_gate({})
    assert result.status == "PROPOSED"
