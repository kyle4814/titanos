def test_portal_roles_contract():
    from titanos_stub import execute_portal_roles
    assert execute_portal_roles(None).status == "REJECT"
    assert execute_portal_roles({}).status == "PROPOSED"
