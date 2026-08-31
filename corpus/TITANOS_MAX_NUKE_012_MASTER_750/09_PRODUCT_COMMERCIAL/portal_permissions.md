def test_portal_permissions_contract():
    from titanos_stub import validate_portal_permissions
    assert validate_portal_permissions({})["status"] == "PROPOSED"
