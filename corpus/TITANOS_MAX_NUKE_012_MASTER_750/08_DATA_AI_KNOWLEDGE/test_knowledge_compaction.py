def test_knowledge_compaction_contract():
    from titanos_stub import validate_knowledge_compaction
    assert validate_knowledge_compaction({})["status"] == "PROPOSED"
