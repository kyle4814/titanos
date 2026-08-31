def test_model_registry_contract():
    from titanos_stub import validate_model_registry
    assert validate_model_registry({})["status"] == "PROPOSED"
