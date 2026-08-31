def test_cancellation_model_contract():
    from titanos_stub import validate_cancellation_model
    assert validate_cancellation_model({})["status"] == "PROPOSED"
