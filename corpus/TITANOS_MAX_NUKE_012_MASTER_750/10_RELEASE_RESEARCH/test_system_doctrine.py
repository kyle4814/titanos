def test_system_doctrine_contract():
    from titanos_stub import validate_system_doctrine
    assert validate_system_doctrine({})["status"] == "PROPOSED"
