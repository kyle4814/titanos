def test_search_eval_contract():
    from titanos_stub import execute_search_eval
    assert execute_search_eval(None).status == "REJECT"
    assert execute_search_eval({}).status == "PROPOSED"
