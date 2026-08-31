def test_benchmark_regression_contract():
    from titanos_stub import validate_benchmark_regression
    assert validate_benchmark_regression({})["status"] == "PROPOSED"
