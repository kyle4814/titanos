from titanos_core.rail import validate_transition

def test_rail_sequential():
    assert validate_transition("LOAD", "CENSUS")

def test_rail_rejects_skip():
    try:
        validate_transition("LOAD", "IMPLEMENT")
    except ValueError:
        return
    raise AssertionError("rail accepted a non-sequential transition")
