def test_metric_definition_contract():
    from titanos_stub import observe_metric_definition
    assert observe_metric_definition({})["status"] == "OBSERVED"
