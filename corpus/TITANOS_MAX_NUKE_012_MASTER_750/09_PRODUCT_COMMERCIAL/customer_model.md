def test_customer_model_contract():
    from titanos_stub import validate_customer_model
    assert validate_customer_model({})["status"] == "PROPOSED"
