def test_scorecard_contract():
    from titanos_stub import validate_scorecard
    assert validate_scorecard({})["status"] == "PROPOSED"
