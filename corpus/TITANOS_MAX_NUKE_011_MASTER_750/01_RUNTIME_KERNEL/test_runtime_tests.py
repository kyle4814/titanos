def test_runtime_tests_contract():
    from titanos_stub import execute_runtime_tests
    assert execute_runtime_tests(None).status == "REJECT"
    assert execute_runtime_tests({}).status == "PROPOSED"
