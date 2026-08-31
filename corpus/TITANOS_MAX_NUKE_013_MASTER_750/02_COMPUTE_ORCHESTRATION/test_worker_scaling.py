def test_worker_scaling_contract():
    from titanos_stub import validate_worker_scaling
    assert validate_worker_scaling({})["status"] == "PROPOSED"
