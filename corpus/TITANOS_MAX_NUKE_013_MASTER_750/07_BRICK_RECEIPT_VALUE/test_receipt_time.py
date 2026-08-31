def test_receipt_time_contract():
    from titanos_stub import validate_receipt_time
    assert validate_receipt_time({})["status"] == "PROPOSED"
