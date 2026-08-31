def test_api_customer_contract():
    from titanos_stub import execute_api_customer
    assert execute_api_customer(None).status == "REJECT"
    assert execute_api_customer({}).status == "PROPOSED"
