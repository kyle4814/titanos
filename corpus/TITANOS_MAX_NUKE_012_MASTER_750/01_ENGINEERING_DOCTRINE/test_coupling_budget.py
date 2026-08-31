def test_coupling_budget_contract():
    from titanos_stub import validate_coupling_budget
    assert validate_coupling_budget({})["status"] == "PROPOSED"
