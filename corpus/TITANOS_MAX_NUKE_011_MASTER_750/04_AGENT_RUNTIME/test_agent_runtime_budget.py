def test_agent_runtime_budget_contract():
    from titanos_stub import execute_agent_runtime_budget
    assert execute_agent_runtime_budget(None).status == "REJECT"
    assert execute_agent_runtime_budget({}).status == "PROPOSED"
