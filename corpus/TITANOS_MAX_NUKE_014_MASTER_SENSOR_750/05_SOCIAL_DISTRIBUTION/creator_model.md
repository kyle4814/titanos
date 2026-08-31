def test_creator_model_contract():
    from titanos_stub import observe_creator_model
    assert observe_creator_model({})["status"] == "OBSERVED"
