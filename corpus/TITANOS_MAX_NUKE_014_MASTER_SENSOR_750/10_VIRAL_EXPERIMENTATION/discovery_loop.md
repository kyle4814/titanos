def test_discovery_loop_contract():
    from titanos_stub import observe_discovery_loop
    assert observe_discovery_loop({})["status"] == "OBSERVED"
