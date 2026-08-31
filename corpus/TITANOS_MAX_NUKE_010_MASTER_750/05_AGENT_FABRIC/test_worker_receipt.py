"""Contract tests for worker_receipt.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_worker_receipt_rejects_invalid_input():
    from titanos_stub import execute_worker_receipt
    result = execute_worker_receipt(None)
    assert result.status == "REJECT"

def test_worker_receipt_does_not_claim_implementation():
    from titanos_stub import execute_worker_receipt
    result = execute_worker_receipt({})
    assert result.status == "PROPOSED"
