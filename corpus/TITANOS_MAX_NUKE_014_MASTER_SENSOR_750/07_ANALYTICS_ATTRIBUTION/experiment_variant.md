def test_experiment_variant_contract():
    from titanos_stub import observe_experiment_variant
    assert observe_experiment_variant({})["status"] == "OBSERVED"
