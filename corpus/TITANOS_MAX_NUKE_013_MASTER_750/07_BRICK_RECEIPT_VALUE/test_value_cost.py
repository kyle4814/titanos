def test_value_cost_contract():
    from titanos_stub import validate_value_cost
    assert validate_value_cost({})["status"] == "PROPOSED"
