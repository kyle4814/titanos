def test_ai_diff_contract():
    from titanos_stub import observe_ai_diff
    assert observe_ai_diff({})["status"] == "OBSERVED"
