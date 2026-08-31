def test_customer_state_contract():
    from titanos_stub import validate_customer_state
    assert validate_customer_state({})["status"] == "PROPOSED"
