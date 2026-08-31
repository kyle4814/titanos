def test_data_retention_contract():
    from titanos_stub import validate_data_retention
    assert validate_data_retention({})["status"] == "PROPOSED"
