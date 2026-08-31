def test_content_caption_contract():
    from titanos_stub import observe_content_caption
    assert observe_content_caption({})["status"] == "OBSERVED"
