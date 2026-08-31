def test_release_rollback_contract():
    from titanos_stub import validate_release_rollback
    assert validate_release_rollback({})["status"] == "PROPOSED"
