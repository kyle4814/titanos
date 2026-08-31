def test_receipt_timestamp_contract():
    from titanos_stub import validate_receipt_timestamp
    assert validate_receipt_timestamp({})["status"] == "PROPOSED"
