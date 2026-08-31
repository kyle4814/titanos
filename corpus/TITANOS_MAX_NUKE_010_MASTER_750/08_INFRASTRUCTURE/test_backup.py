"""Contract tests for backup.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_backup_rejects_invalid_input():
    from titanos_stub import execute_backup
    result = execute_backup(None)
    assert result.status == "REJECT"

def test_backup_does_not_claim_implementation():
    from titanos_stub import execute_backup
    result = execute_backup({})
    assert result.status == "PROPOSED"
