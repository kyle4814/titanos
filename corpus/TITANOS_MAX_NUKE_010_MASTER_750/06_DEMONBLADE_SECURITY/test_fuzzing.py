"""Contract tests for fuzzing.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_fuzzing_rejects_invalid_input():
    from titanos_stub import execute_fuzzing
    result = execute_fuzzing(None)
    assert result.status == "REJECT"

def test_fuzzing_does_not_claim_implementation():
    from titanos_stub import execute_fuzzing
    result = execute_fuzzing({})
    assert result.status == "PROPOSED"
