def test_sla_contract():
    from titanos_stub import validate_sla
    assert validate_sla({})["status"] == "PROPOSED"
