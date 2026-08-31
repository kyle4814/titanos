"""Contract tests for receipt_baseline.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_receipt_baseline_rejects_invalid_input():
    from titanos_stub import execute_receipt_baseline
    result = execute_receipt_baseline(None)
    assert result.status == "REJECT"

def test_receipt_baseline_does_not_claim_implementation():
    from titanos_stub import execute_receipt_baseline
    result = execute_receipt_baseline({})
    assert result.status == "PROPOSED"
