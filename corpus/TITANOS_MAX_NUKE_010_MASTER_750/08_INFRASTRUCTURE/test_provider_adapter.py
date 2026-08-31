"""Contract tests for provider_adapter.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_provider_adapter_rejects_invalid_input():
    from titanos_stub import execute_provider_adapter
    result = execute_provider_adapter(None)
    assert result.status == "REJECT"

def test_provider_adapter_does_not_claim_implementation():
    from titanos_stub import execute_provider_adapter
    result = execute_provider_adapter({})
    assert result.status == "PROPOSED"
