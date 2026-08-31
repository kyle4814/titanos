"""Contract tests for golden_tests.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_golden_tests_rejects_invalid_input():
    from titanos_stub import execute_golden_tests
    result = execute_golden_tests(None)
    assert result.status == "REJECT"

def test_golden_tests_does_not_claim_implementation():
    from titanos_stub import execute_golden_tests
    result = execute_golden_tests({})
    assert result.status == "PROPOSED"
