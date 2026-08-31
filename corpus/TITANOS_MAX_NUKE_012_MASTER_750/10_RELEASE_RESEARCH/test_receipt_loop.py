def test_receipt_loop_contract():
    from titanos_stub import validate_receipt_loop
    assert validate_receipt_loop({})["status"] == "PROPOSED"
