def test_data_privacy_contract():
    from titanos_stub import execute_data_privacy
    assert execute_data_privacy(None).status == "REJECT"
    assert execute_data_privacy({}).status == "PROPOSED"
