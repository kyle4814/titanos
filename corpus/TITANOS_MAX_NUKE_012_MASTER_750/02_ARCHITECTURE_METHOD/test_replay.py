def test_replay_contract():
    from titanos_stub import validate_replay
    assert validate_replay({})["status"] == "PROPOSED"
