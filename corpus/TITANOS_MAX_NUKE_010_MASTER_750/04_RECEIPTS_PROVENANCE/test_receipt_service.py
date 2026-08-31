"""Contract tests for receipt_service.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_receipt_service_rejects_invalid_input():
    from titanos_stub import execute_receipt_service
    result = execute_receipt_service(None)
    assert result.status == "REJECT"

def test_receipt_service_does_not_claim_implementation():
    from titanos_stub import execute_receipt_service
    result = execute_receipt_service({})
    assert result.status == "PROPOSED"
