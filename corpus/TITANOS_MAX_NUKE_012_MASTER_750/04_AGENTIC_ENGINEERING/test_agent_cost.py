def test_agent_cost_contract():
    from titanos_stub import validate_agent_cost
    assert validate_agent_cost({})["status"] == "PROPOSED"
