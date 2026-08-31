def test_value_engine_runbook_contract():
    from titanos_stub import execute_value_engine_runbook
    assert execute_value_engine_runbook(None).status == "REJECT"
    assert execute_value_engine_runbook({}).status == "PROPOSED"
