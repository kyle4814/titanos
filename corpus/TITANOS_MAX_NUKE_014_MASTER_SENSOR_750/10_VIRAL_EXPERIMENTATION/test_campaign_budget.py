def test_campaign_budget_contract():
    from titanos_stub import observe_campaign_budget
    assert observe_campaign_budget({})["status"] == "OBSERVED"
