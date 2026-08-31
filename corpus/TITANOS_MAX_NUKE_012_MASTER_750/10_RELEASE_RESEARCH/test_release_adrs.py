def test_release_adrs_contract():
    from titanos_stub import validate_release_adrs
    assert validate_release_adrs({})["status"] == "PROPOSED"
