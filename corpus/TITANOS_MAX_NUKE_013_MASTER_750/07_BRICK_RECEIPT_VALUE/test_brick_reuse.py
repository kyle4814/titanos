def test_brick_reuse_contract():
    from titanos_stub import validate_brick_reuse
    assert validate_brick_reuse({})["status"] == "PROPOSED"
