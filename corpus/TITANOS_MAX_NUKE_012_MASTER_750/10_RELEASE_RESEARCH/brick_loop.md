def test_brick_loop_contract():
    from titanos_stub import validate_brick_loop
    assert validate_brick_loop({})["status"] == "PROPOSED"
