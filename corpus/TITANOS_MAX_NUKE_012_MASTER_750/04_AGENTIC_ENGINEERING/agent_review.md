def test_agent_review_contract():
    from titanos_stub import validate_agent_review
    assert validate_agent_review({})["status"] == "PROPOSED"
