"""Contract tests for churn_model.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_churn_model_rejects_invalid_input():
    from titanos_stub import execute_churn_model
    result = execute_churn_model(None)
    assert result.status == "REJECT"

def test_churn_model_does_not_claim_implementation():
    from titanos_stub import execute_churn_model
    result = execute_churn_model({})
    assert result.status == "PROPOSED"
