"""Contract tests for migration.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_migration_rejects_invalid_input():
    from titanos_stub import execute_migration
    result = execute_migration(None)
    assert result.status == "REJECT"

def test_migration_does_not_claim_implementation():
    from titanos_stub import execute_migration
    result = execute_migration({})
    assert result.status == "PROPOSED"
