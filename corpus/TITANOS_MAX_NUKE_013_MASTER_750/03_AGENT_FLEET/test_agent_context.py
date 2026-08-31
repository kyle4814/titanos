def test_agent_context_contract():
    from titanos_stub import validate_agent_context
    assert validate_agent_context({})["status"] == "PROPOSED"
