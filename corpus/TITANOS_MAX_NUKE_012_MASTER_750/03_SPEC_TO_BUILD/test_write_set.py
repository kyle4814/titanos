def test_write_set_contract():
    from titanos_stub import validate_write_set
    assert validate_write_set({})["status"] == "PROPOSED"
