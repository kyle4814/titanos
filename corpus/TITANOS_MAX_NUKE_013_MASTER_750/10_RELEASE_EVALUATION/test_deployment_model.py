def test_deployment_model_contract():
    from titanos_stub import validate_deployment_model
    assert validate_deployment_model({})["status"] == "PROPOSED"
