def test_security_receipt_contract():
    from titanos_stub import validate_security_receipt
    assert validate_security_receipt({})["status"] == "PROPOSED"
