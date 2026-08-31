from pathlib import Path
import importlib.util
def load_state_machine():
    p = Path(__file__).parents[1] / "01_kernel" / "state_machine.py"
    spec = importlib.util.spec_from_file_location("state_machine", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
