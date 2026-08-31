"""Contract tests for evidence_capture.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_evidence_capture_rejects_invalid_input():
    from titanos_stub import execute_evidence_capture
    result = execute_evidence_capture(None)
    assert result.status == "REJECT"

def test_evidence_capture_does_not_claim_implementation():
    from titanos_stub import execute_evidence_capture
    result = execute_evidence_capture({})
    assert result.status == "PROPOSED"
