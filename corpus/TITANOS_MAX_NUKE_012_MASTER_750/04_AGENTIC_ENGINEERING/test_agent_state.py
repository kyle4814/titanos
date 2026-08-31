def test_agent_state_contract():
    from titanos_stub import validate_agent_state
    assert validate_agent_state({})["status"] == "PROPOSED"
