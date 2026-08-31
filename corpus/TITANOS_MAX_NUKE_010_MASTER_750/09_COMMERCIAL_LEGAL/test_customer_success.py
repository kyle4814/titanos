"""Contract tests for customer_success.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_customer_success_rejects_invalid_input():
    from titanos_stub import execute_customer_success
    result = execute_customer_success(None)
    assert result.status == "REJECT"

def test_customer_success_does_not_claim_implementation():
    from titanos_stub import execute_customer_success
    result = execute_customer_success({})
    assert result.status == "PROPOSED"
