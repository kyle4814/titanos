def test_billing_event_contract():
    from titanos_stub import execute_billing_event
    assert execute_billing_event(None).status == "REJECT"
    assert execute_billing_event({}).status == "PROPOSED"
