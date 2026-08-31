def test_impression_model_contract():
    from titanos_stub import observe_impression_model
    assert observe_impression_model({})["status"] == "OBSERVED"
