def test_complexity_budget_contract():
    from titanos_stub import validate_complexity_budget
    assert validate_complexity_budget({})["status"] == "PROPOSED"
