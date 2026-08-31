def test_node_state_contract():
    from titanos_stub import validate_node_state
    assert validate_node_state({})["status"] == "PROPOSED"
