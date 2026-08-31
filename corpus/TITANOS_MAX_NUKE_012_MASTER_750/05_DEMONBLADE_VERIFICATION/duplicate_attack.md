def test_duplicate_attack_contract():
    from titanos_stub import validate_duplicate_attack
    assert validate_duplicate_attack({})["status"] == "PROPOSED"
