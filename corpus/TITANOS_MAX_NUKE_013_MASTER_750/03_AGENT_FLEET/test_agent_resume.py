def test_agent_resume_contract():
    from titanos_stub import validate_agent_resume
    assert validate_agent_resume({})["status"] == "PROPOSED"
