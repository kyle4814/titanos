"""Contract tests for attack_surface.

These tests establish the minimum interface contract; production behaviour
must be implemented and expanded by the relevant worker.
"""
def test_attack_surface_rejects_invalid_input():
    from titanos_stub import execute_attack_surface
    result = execute_attack_surface(None)
    assert result.status == "REJECT"

def test_attack_surface_does_not_claim_implementation():
    from titanos_stub import execute_attack_surface
    result = execute_attack_surface({})
    assert result.status == "PROPOSED"
