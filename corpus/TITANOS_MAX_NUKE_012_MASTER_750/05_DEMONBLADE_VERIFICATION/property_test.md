def test_property_test_contract():
    from titanos_stub import validate_property_test
    assert validate_property_test({})["status"] == "PROPOSED"
