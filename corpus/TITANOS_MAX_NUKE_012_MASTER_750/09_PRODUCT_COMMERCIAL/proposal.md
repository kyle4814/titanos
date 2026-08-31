def test_proposal_contract():
    from titanos_stub import validate_proposal
    assert validate_proposal({})["status"] == "PROPOSED"
