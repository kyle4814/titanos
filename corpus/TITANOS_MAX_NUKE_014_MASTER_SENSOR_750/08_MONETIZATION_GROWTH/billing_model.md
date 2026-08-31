def test_billing_model_contract():
    from titanos_stub import observe_billing_model
    assert observe_billing_model({})["status"] == "OBSERVED"
