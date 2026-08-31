def test_campaign_objective_contract():
    from titanos_stub import observe_campaign_objective
    assert observe_campaign_objective({})["status"] == "OBSERVED"
