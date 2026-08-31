def test_governance_change_contract():
    from titanos_stub import validate_governance_change
    assert validate_governance_change({})["status"] == "PROPOSED"
