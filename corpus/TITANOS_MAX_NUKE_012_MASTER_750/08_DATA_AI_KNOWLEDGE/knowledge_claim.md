def test_knowledge_claim_contract():
    from titanos_stub import validate_knowledge_claim
    assert validate_knowledge_claim({})["status"] == "PROPOSED"
