def test_portal_feature_flags_contract():
    from titanos_stub import execute_portal_feature_flags
    assert execute_portal_feature_flags(None).status == "REJECT"
    assert execute_portal_feature_flags({}).status == "PROPOSED"
