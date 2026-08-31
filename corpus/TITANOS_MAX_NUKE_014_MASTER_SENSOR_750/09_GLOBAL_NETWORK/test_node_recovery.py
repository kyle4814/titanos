def test_node_recovery_contract():
    from titanos_stub import observe_node_recovery
    assert observe_node_recovery({})["status"] == "OBSERVED"
