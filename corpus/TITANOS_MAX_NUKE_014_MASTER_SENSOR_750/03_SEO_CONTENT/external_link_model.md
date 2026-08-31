def test_external_link_model_contract():
    from titanos_stub import observe_external_link_model
    assert observe_external_link_model({})["status"] == "OBSERVED"
