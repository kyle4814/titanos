def test_ai_budget_contract():
    from titanos_stub import validate_ai_budget
    assert validate_ai_budget({})["status"] == "PROPOSED"
