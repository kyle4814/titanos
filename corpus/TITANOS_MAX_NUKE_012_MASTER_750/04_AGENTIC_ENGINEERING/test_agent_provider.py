def test_agent_provider_contract():
    from titanos_stub import validate_agent_provider
    assert validate_agent_provider({})["status"] == "PROPOSED"
