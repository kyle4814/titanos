def test_metric_discipline_contract():
    from titanos_stub import validate_metric_discipline
    assert validate_metric_discipline({})["status"] == "PROPOSED"
