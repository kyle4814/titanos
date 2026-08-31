def test_entity_alias_contract():
    from titanos_stub import observe_entity_alias
    assert observe_entity_alias({})["status"] == "OBSERVED"
