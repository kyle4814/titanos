def test_discovery_state_contract():
    from titanos_stub import observe_discovery_state
    assert observe_discovery_state({})["status"] == "OBSERVED"
