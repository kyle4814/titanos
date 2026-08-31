def test_portal_metrics_contract():
    from titanos_stub import validate_portal_metrics
    assert validate_portal_metrics({})["status"] == "PROPOSED"
