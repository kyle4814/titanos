def test_agent_receipt_contract():
    from titanos_stub import validate_agent_receipt
    assert validate_agent_receipt({})["status"] == "PROPOSED"
