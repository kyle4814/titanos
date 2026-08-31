"""Contract tests for ato_checklist.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_ato_checklist_rejects_invalid_input():
    from titanos_stub import execute_ato_checklist
    result = execute_ato_checklist(None)
    assert result.status == "REJECT"

def test_ato_checklist_does_not_claim_implementation():
    from titanos_stub import execute_ato_checklist
    result = execute_ato_checklist({})
    assert result.status == "PROPOSED"
