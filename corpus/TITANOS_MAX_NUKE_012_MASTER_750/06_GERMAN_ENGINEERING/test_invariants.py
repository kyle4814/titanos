def test_invariants_contract():
    from titanos_stub import validate_invariants
    assert validate_invariants({})["status"] == "PROPOSED"
