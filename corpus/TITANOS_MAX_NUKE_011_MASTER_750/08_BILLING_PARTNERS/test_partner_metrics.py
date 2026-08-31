def test_partner_metrics_contract():
    from titanos_stub import execute_partner_metrics
    assert execute_partner_metrics(None).status == "REJECT"
    assert execute_partner_metrics({}).status == "PROPOSED"
