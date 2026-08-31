def test_case_study_model_contract():
    from titanos_stub import observe_case_study_model
    assert observe_case_study_model({})["status"] == "OBSERVED"
