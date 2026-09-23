import tempfile, unittest
from pathlib import Path
from foundation.dispatcher_state import DispatcherState, DispatcherStateStore

class TestDispatcherState(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            s=DispatcherStateStore(Path(td)/"dispatcher.json")
            state=DispatcherState("p1",("a",),("b",),("c",),("d",))
            s.save(state); self.assertEqual(s.load("p1"),state)
    def test_pool_identity(self):
        with tempfile.TemporaryDirectory() as td:
            s=DispatcherStateStore(Path(td)/"dispatcher.json"); s.save(DispatcherState("p1"))
            with self.assertRaises(ValueError): s.load("p2")
if __name__=="__main__": unittest.main()
