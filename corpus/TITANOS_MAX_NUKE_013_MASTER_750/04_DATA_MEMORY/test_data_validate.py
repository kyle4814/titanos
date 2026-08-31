def test_data_validate_contract():
    from titanos_stub import validate_data_validate
    assert validate_data_validate({})["status"] == "PROPOSED"
