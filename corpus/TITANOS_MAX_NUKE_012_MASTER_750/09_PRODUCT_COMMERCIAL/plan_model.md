def test_plan_model_contract():
    from titanos_stub import validate_plan_model
    assert validate_plan_model({})["status"] == "PROPOSED"
