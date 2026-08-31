"""Contract tests for state_machine.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_state_machine_rejects_invalid_input():
    from titanos_stub import execute_state_machine
    result = execute_state_machine(None)
    assert result.status == "REJECT"

def test_state_machine_does_not_claim_implementation():
    from titanos_stub import execute_state_machine
    result = execute_state_machine({})
    assert result.status == "PROPOSED"
