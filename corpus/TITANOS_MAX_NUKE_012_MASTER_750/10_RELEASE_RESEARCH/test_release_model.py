def test_release_model_contract():
    from titanos_stub import validate_release_model
    assert validate_release_model({})["status"] == "PROPOSED"
