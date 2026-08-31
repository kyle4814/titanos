def test_agent_runbook_contract():
    from titanos_stub import validate_agent_runbook
    assert validate_agent_runbook({})["status"] == "PROPOSED"
