def test_node_registry_contract():
    from titanos_stub import observe_node_registry
    assert observe_node_registry({})["status"] == "OBSERVED"
