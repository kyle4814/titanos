def test_root_cause_contract():
    from titanos_stub import validate_root_cause
    assert validate_root_cause({})["status"] == "PROPOSED"
