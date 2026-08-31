def test_node_shutdown_contract():
    from titanos_stub import validate_node_shutdown
    assert validate_node_shutdown({})["status"] == "PROPOSED"
