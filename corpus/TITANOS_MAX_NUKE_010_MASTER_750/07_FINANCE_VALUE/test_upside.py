"""Contract tests for upside.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_upside_rejects_invalid_input():
    from titanos_stub import execute_upside
    result = execute_upside(None)
    assert result.status == "REJECT"

def test_upside_does_not_claim_implementation():
    from titanos_stub import execute_upside
    result = execute_upside({})
    assert result.status == "PROPOSED"
