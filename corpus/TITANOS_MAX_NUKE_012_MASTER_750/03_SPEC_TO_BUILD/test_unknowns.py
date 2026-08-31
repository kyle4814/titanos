def test_unknowns_contract():
    from titanos_stub import validate_unknowns
    assert validate_unknowns({})["status"] == "PROPOSED"
