def test_governance_adrs_contract():
    from titanos_stub import validate_governance_adrs
    assert validate_governance_adrs({})["status"] == "PROPOSED"
