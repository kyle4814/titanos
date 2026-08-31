"""Contract tests for founders_agreement.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_founders_agreement_rejects_invalid_input():
    from titanos_stub import execute_founders_agreement
    result = execute_founders_agreement(None)
    assert result.status == "REJECT"

def test_founders_agreement_does_not_claim_implementation():
    from titanos_stub import execute_founders_agreement
    result = execute_founders_agreement({})
    assert result.status == "PROPOSED"
