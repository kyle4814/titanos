def test_crawler_hash_contract():
    from titanos_stub import observe_crawler_hash
    assert observe_crawler_hash({})["status"] == "OBSERVED"
