def test_portal_navigation_contract():
    from titanos_stub import validate_portal_navigation
    assert validate_portal_navigation({})["status"] == "PROPOSED"
