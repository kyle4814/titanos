def test_contracts_contract():
    from titanos_stub import validate_contracts
    assert validate_contracts({})["status"] == "PROPOSED"
