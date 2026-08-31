def test_data_authorization_contract():
    from titanos_stub import execute_data_authorization
    assert execute_data_authorization(None).status == "REJECT"
    assert execute_data_authorization({}).status == "PROPOSED"
