"""Contract tests for human_review.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_human_review_rejects_invalid_input():
    from titanos_stub import execute_human_review
    result = execute_human_review(None)
    assert result.status == "REJECT"

def test_human_review_does_not_claim_implementation():
    from titanos_stub import execute_human_review
    result = execute_human_review({})
    assert result.status == "PROPOSED"
