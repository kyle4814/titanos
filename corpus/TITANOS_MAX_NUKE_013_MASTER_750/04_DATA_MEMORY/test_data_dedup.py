def test_data_dedup_contract():
    from titanos_stub import validate_data_dedup
    assert validate_data_dedup({})["status"] == "PROPOSED"
