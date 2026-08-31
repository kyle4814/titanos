def test_content_cta_contract():
    from titanos_stub import observe_content_cta
    assert observe_content_cta({})["status"] == "OBSERVED"
