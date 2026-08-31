def test_evaluation_runbook_contract():
    from titanos_stub import validate_evaluation_runbook
    assert validate_evaluation_runbook({})["status"] == "PROPOSED"
