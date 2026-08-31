def test_crawler_scheduler_contract():
    from titanos_stub import observe_crawler_scheduler
    assert observe_crawler_scheduler({})["status"] == "OBSERVED"
