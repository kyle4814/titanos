def test_model_release_contract():
    from titanos_stub import validate_model_release
    assert validate_model_release({})["status"] == "PROPOSED"
