def test_billing_cancellation_contract():
    from titanos_stub import execute_billing_cancellation
    assert execute_billing_cancellation(None).status == "REJECT"
    assert execute_billing_cancellation({}).status == "PROPOSED"
