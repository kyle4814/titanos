def test_review_checklist_contract():
    from titanos_stub import validate_review_checklist
    assert validate_review_checklist({})["status"] == "PROPOSED"
