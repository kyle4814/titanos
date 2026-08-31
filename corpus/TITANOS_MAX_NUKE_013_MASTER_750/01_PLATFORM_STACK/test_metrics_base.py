def test_metrics_base_contract():
    from titanos_stub import validate_metrics_base
    assert validate_metrics_base({})["status"] == "PROPOSED"
