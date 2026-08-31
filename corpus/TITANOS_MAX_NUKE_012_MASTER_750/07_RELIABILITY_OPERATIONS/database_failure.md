def test_database_failure_contract():
    from titanos_stub import validate_database_failure
    assert validate_database_failure({})["status"] == "PROPOSED"
