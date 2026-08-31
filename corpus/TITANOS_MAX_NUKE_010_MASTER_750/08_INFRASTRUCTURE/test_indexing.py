"""Contract tests for indexing.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_indexing_rejects_invalid_input():
    from titanos_stub import execute_indexing
    result = execute_indexing(None)
    assert result.status == "REJECT"

def test_indexing_does_not_claim_implementation():
    from titanos_stub import execute_indexing
    result = execute_indexing({})
    assert result.status == "PROPOSED"
