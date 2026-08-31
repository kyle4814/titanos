"""Contract tests for sbom.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_sbom_rejects_invalid_input():
    from titanos_stub import execute_sbom
    result = execute_sbom(None)
    assert result.status == "REJECT"

def test_sbom_does_not_claim_implementation():
    from titanos_stub import execute_sbom
    result = execute_sbom({})
    assert result.status == "PROPOSED"
