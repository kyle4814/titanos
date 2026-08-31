def test_release_runbook_contract():
    from titanos_stub import validate_release_runbook
    assert validate_release_runbook({})["status"] == "PROPOSED"
