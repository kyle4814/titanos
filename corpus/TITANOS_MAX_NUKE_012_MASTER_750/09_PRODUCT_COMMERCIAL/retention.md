def test_retention_contract():
    from titanos_stub import validate_retention
    assert validate_retention({})["status"] == "PROPOSED"
