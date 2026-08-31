def test_growth_alert_contract():
    from titanos_stub import observe_growth_alert
    assert observe_growth_alert({})["status"] == "OBSERVED"
