def test_snapshotting_contract():
    from titanos_stub import validate_snapshotting
    assert validate_snapshotting({})["status"] == "PROPOSED"
