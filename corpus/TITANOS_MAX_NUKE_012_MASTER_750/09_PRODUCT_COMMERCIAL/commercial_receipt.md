def test_commercial_receipt_contract():
    from titanos_stub import validate_commercial_receipt
    assert validate_commercial_receipt({})["status"] == "PROPOSED"
