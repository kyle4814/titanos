def test_portal_dashboard_contract():
    from titanos_stub import validate_portal_dashboard
    assert validate_portal_dashboard({})["status"] == "PROPOSED"
