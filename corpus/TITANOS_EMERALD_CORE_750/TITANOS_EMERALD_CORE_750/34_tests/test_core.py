import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _kernel_import import load_state_machine

def test_valid_transition():
    sm = load_state_machine()
    assert sm.transition("QUEUED", "CLAIMED") == "CLAIMED"

def test_invalid_transition():
    sm = load_state_machine()
    try:
        sm.transition("QUEUED", "COMPLETE")
    except ValueError:
        return
    assert False
