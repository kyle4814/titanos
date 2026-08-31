def test_portability_contract():
    from titanos_stub import validate_portability
    assert validate_portability({})["status"] == "PROPOSED"
