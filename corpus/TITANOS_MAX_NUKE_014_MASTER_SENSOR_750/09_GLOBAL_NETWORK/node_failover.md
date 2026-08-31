def test_node_failover_contract():
    from titanos_stub import observe_node_failover
    assert observe_node_failover({})["status"] == "OBSERVED"
