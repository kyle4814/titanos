"""Contract tests for receipt_hash.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_receipt_hash_rejects_invalid_input():
    from titanos_stub import execute_receipt_hash
    result = execute_receipt_hash(None)
    assert result.status == "REJECT"

def test_receipt_hash_does_not_claim_implementation():
    from titanos_stub import execute_receipt_hash
    result = execute_receipt_hash({})
    assert result.status == "PROPOSED"
