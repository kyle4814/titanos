def test_search_snapshot_contract():
    from titanos_stub import execute_search_snapshot
    assert execute_search_snapshot(None).status == "REJECT"
    assert execute_search_snapshot({}).status == "PROPOSED"
