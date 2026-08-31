def test_requirement_tests_contract():
    from titanos_stub import validate_requirement_tests
    assert validate_requirement_tests({})["status"] == "PROPOSED"
