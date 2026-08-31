def test_migration_plan_contract():
    from titanos_stub import validate_migration_plan
    assert validate_migration_plan({})["status"] == "PROPOSED"
