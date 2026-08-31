def test_brick_implementation_contract():
    from titanos_stub import validate_brick_implementation
    assert validate_brick_implementation({})["status"] == "PROPOSED"
