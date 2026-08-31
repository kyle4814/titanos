def test_node_capacity_contract():
    from titanos_stub import observe_node_capacity
    assert observe_node_capacity({})["status"] == "OBSERVED"
