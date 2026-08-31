def test_crawler_provenance_contract():
    from titanos_stub import observe_crawler_provenance
    assert observe_crawler_provenance({})["status"] == "OBSERVED"
