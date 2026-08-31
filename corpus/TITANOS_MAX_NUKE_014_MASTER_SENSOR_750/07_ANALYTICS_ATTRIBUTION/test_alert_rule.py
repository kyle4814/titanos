def test_alert_rule_contract():
    from titanos_stub import observe_alert_rule
    assert observe_alert_rule({})["status"] == "OBSERVED"
