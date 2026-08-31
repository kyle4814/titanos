def test_content_loop_contract():
    from titanos_stub import observe_content_loop
    assert observe_content_loop({})["status"] == "OBSERVED"
