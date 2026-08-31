def test_agent_capacity_contract():
    from titanos_stub import validate_agent_capacity
    assert validate_agent_capacity({})["status"] == "PROPOSED"
