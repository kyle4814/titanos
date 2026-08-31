def test_cost_discipline_contract():
    from titanos_stub import validate_cost_discipline
    assert validate_cost_discipline({})["status"] == "PROPOSED"
