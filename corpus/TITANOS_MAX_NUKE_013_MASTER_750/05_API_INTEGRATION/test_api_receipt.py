def test_api_receipt_contract():
    from titanos_stub import validate_api_receipt
    assert validate_api_receipt({})["status"] == "PROPOSED"
