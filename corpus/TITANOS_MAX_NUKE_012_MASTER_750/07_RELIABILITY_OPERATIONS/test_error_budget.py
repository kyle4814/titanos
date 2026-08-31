def test_error_budget_contract():
    from titanos_stub import validate_error_budget
    assert validate_error_budget({})["status"] == "PROPOSED"
