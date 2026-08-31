def test_dashboards_contract():
    from titanos_stub import validate_dashboards
    assert validate_dashboards({})["status"] == "PROPOSED"
