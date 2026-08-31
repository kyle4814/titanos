def test_research_snapshot_contract():
    from titanos_stub import validate_research_snapshot
    assert validate_research_snapshot({})["status"] == "PROPOSED"
