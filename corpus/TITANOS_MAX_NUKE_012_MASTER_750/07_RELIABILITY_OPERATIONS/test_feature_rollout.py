def test_feature_rollout_contract():
    from titanos_stub import validate_feature_rollout
    assert validate_feature_rollout({})["status"] == "PROPOSED"
