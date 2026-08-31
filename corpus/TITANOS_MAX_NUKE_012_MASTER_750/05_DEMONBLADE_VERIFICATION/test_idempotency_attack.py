def test_idempotency_attack_contract():
    from titanos_stub import validate_idempotency_attack
    assert validate_idempotency_attack({})["status"] == "PROPOSED"
