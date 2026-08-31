def test_compatibility_base_contract():
    from titanos_stub import validate_compatibility_base
    assert validate_compatibility_base({})["status"] == "PROPOSED"
