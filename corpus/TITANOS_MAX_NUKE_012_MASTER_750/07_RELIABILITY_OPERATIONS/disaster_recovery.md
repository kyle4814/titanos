def test_disaster_recovery_contract():
    from titanos_stub import validate_disaster_recovery
    assert validate_disaster_recovery({})["status"] == "PROPOSED"
