def test_quote_contract():
    from titanos_stub import validate_quote
    assert validate_quote({})["status"] == "PROPOSED"
