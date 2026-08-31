def test_agent_evaluation_contract():
    from titanos_stub import validate_agent_evaluation
    assert validate_agent_evaluation({})["status"] == "PROPOSED"
