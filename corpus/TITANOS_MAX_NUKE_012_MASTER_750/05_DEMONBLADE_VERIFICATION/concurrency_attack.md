def test_concurrency_attack_contract():
    from titanos_stub import validate_concurrency_attack
    assert validate_concurrency_attack({})["status"] == "PROPOSED"
