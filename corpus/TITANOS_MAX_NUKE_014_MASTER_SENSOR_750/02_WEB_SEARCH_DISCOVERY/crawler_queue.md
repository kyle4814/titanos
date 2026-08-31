def test_crawler_queue_contract():
    from titanos_stub import observe_crawler_queue
    assert observe_crawler_queue({})["status"] == "OBSERVED"
