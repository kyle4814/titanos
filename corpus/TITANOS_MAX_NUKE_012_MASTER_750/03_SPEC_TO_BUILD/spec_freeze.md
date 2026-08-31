def test_spec_freeze_contract():
    from titanos_stub import validate_spec_freeze
    assert validate_spec_freeze({})["status"] == "PROPOSED"
