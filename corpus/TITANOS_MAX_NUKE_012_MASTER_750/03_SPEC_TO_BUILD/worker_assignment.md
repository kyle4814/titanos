def test_worker_assignment_contract():
    from titanos_stub import validate_worker_assignment
    assert validate_worker_assignment({})["status"] == "PROPOSED"
