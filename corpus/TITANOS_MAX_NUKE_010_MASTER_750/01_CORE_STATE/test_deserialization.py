"""Contract tests for deserialization.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_deserialization_rejects_invalid_input():
    from titanos_stub import execute_deserialization
    result = execute_deserialization(None)
    assert result.status == "REJECT"

def test_deserialization_does_not_claim_implementation():
    from titanos_stub import execute_deserialization
    result = execute_deserialization({})
    assert result.status == "PROPOSED"
