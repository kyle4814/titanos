"""Contract tests for receipt_adrs.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_receipt_adrs_rejects_invalid_input():
    from titanos_stub import execute_receipt_adrs
    result = execute_receipt_adrs(None)
    assert result.status == "REJECT"

def test_receipt_adrs_does_not_claim_implementation():
    from titanos_stub import execute_receipt_adrs
    result = execute_receipt_adrs({})
    assert result.status == "PROPOSED"
