def test_data_pipeline_tests_contract():
    from titanos_stub import execute_data_pipeline_tests
    assert execute_data_pipeline_tests(None).status == "REJECT"
    assert execute_data_pipeline_tests({}).status == "PROPOSED"
