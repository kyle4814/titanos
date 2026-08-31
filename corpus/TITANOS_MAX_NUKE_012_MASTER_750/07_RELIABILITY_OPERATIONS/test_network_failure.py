def test_network_failure_contract():
    from titanos_stub import validate_network_failure
    assert validate_network_failure({})["status"] == "PROPOSED"
