def test_runtime_signal_contract():
    from titanos_stub import execute_runtime_signal
    assert execute_runtime_signal(None).status == "REJECT"
    assert execute_runtime_signal({}).status == "PROPOSED"
