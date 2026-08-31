def test_agent_safety_contract():
    from titanos_stub import validate_agent_safety
    assert validate_agent_safety({})["status"] == "PROPOSED"
