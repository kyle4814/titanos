def test_deprecation_discipline_contract():
    from titanos_stub import validate_deprecation_discipline
    assert validate_deprecation_discipline({})["status"] == "PROPOSED"
