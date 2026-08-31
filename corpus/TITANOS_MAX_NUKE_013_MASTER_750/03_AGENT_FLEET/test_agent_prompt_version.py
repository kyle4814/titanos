def test_agent_prompt_version_contract():
    from titanos_stub import validate_agent_prompt_version
    assert validate_agent_prompt_version({})["status"] == "PROPOSED"
