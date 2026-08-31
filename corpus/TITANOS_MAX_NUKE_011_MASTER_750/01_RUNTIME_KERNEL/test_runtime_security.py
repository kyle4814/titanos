def test_runtime_security_contract():
    from titanos_stub import execute_runtime_security
    assert execute_runtime_security(None).status == "REJECT"
    assert execute_runtime_security({}).status == "PROPOSED"
