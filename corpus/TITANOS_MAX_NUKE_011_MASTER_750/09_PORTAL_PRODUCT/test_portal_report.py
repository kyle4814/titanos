def test_portal_report_contract():
    from titanos_stub import execute_portal_report
    assert execute_portal_report(None).status == "REJECT"
    assert execute_portal_report({}).status == "PROPOSED"
