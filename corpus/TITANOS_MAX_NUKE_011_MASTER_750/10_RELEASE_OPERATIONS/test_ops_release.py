def test_ops_release_contract():
    from titanos_stub import execute_ops_release
    assert execute_ops_release(None).status == "REJECT"
    assert execute_ops_release({}).status == "PROPOSED"
