import tempfile, unittest
from pathlib import Path
from foundation.swarm_state import SwarmState, SwarmStateStore

class TestSwarmState(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            s=SwarmStateStore(Path(td)/"swarm.json")
            state=SwarmState("s1",("a",),("b","c"),("d",),("e",))
            s.save(state)
            self.assertEqual(s.load("s1"),state)
    def test_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=SwarmStateStore(Path(td)/"swarm.json")
            s.save(SwarmState("s1"))
            with self.assertRaises(ValueError): s.load("s2")

if __name__=="__main__": unittest.main()
