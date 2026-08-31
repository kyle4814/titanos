def test_distribution_roi_contract():
    from titanos_stub import observe_distribution_roi
    assert observe_distribution_roi({})["status"] == "OBSERVED"
