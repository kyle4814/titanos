def test_node_receipts_contract():
    from titanos_stub import validate_node_receipts
    assert validate_node_receipts({})["status"] == "PROPOSED"
