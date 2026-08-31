"""Contract tests for healthcheck.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_healthcheck_rejects_invalid_input():
    from titanos_stub import execute_healthcheck
    result = execute_healthcheck(None)
    assert result.status == "REJECT"

def test_healthcheck_does_not_claim_implementation():
    from titanos_stub import execute_healthcheck
    result = execute_healthcheck({})
    assert result.status == "PROPOSED"
