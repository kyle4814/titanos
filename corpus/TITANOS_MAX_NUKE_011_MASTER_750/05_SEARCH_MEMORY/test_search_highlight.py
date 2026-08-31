def test_search_highlight_contract():
    from titanos_stub import execute_search_highlight
    assert execute_search_highlight(None).status == "REJECT"
    assert execute_search_highlight({}).status == "PROPOSED"
