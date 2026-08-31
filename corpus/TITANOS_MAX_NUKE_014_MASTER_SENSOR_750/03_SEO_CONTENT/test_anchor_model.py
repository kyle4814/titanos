def test_anchor_model_contract():
    from titanos_stub import observe_anchor_model
    assert observe_anchor_model({})["status"] == "OBSERVED"
