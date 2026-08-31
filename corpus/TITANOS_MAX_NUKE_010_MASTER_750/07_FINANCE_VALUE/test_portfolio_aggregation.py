"""Contract tests for portfolio_aggregation.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_portfolio_aggregation_rejects_invalid_input():
    from titanos_stub import execute_portfolio_aggregation
    result = execute_portfolio_aggregation(None)
    assert result.status == "REJECT"

def test_portfolio_aggregation_does_not_claim_implementation():
    from titanos_stub import execute_portfolio_aggregation
    result = execute_portfolio_aggregation({})
    assert result.status == "PROPOSED"
