def test_postmortem_contract():
    from titanos_stub import validate_postmortem
    assert validate_postmortem({})["status"] == "PROPOSED"
