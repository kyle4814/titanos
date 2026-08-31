def test_execution_replay_contract():
    from titanos_stub import validate_execution_replay
    assert validate_execution_replay({})["status"] == "PROPOSED"
