def test_testability_contract():
    from titanos_stub import validate_testability
    assert validate_testability({})["status"] == "PROPOSED"
