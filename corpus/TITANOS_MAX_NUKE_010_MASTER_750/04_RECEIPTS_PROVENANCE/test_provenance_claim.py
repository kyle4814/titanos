"""Contract tests for provenance_claim.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_provenance_claim_rejects_invalid_input():
    from titanos_stub import execute_provenance_claim
    result = execute_provenance_claim(None)
    assert result.status == "REJECT"

def test_provenance_claim_does_not_claim_implementation():
    from titanos_stub import execute_provenance_claim
    result = execute_provenance_claim({})
    assert result.status == "PROPOSED"
