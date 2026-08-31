def test_privacy_deletion_contract():
    from titanos_stub import execute_privacy_deletion
    assert execute_privacy_deletion(None).status == "REJECT"
    assert execute_privacy_deletion({}).status == "PROPOSED"
