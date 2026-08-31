def test_social_policy_contract():
    from titanos_stub import observe_social_policy
    assert observe_social_policy({})["status"] == "OBSERVED"
