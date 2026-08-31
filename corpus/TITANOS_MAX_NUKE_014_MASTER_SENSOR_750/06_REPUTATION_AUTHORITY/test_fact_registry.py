def test_fact_registry_contract():
    from titanos_stub import observe_fact_registry
    assert observe_fact_registry({})["status"] == "OBSERVED"
