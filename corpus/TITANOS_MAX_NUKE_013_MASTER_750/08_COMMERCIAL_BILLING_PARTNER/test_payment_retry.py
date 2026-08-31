def test_payment_retry_contract():
    from titanos_stub import validate_payment_retry
    assert validate_payment_retry({})["status"] == "PROPOSED"
