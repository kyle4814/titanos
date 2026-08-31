def test_ops_restore_contract():
    from titanos_stub import execute_ops_restore
    assert execute_ops_restore(None).status == "REJECT"
    assert execute_ops_restore({}).status == "PROPOSED"
