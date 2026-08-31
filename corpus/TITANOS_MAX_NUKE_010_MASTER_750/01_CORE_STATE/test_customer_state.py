"""Contract tests for customer_state.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_customer_state_rejects_invalid_input():
    from titanos_stub import execute_customer_state
    result = execute_customer_state(None)
    assert result.status == "REJECT"

def test_customer_state_does_not_claim_implementation():
    from titanos_stub import execute_customer_state
    result = execute_customer_state({})
    assert result.status == "PROPOSED"
