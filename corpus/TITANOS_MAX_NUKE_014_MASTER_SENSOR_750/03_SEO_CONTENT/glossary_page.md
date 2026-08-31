def test_glossary_page_contract():
    from titanos_stub import observe_glossary_page
    assert observe_glossary_page({})["status"] == "OBSERVED"
