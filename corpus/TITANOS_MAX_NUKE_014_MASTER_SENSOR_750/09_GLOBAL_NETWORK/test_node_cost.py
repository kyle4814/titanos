def test_node_cost_contract():
    from titanos_stub import observe_node_cost
    assert observe_node_cost({})["status"] == "OBSERVED"
