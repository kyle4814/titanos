def test_api_job_contract():
    from titanos_stub import validate_api_job
    assert validate_api_job({})["status"] == "PROPOSED"
