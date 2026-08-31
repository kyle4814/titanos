def test_network_alert_contract():
    from titanos_stub import observe_network_alert
    assert observe_network_alert({})["status"] == "OBSERVED"
