"""Contract tests for agent_examples.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_agent_examples_rejects_invalid_input():
    from titanos_stub import execute_agent_examples
    result = execute_agent_examples(None)
    assert result.status == "REJECT"

def test_agent_examples_does_not_claim_implementation():
    from titanos_stub import execute_agent_examples
    result = execute_agent_examples({})
    assert result.status == "PROPOSED"
