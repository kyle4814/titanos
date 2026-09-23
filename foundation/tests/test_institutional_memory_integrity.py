import json,tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
class TestInstitutionalMemoryIntegrity(unittest.TestCase):
    def test_checksum_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; s=InstitutionalMemoryStore(p); s.save(InstitutionalMemory())
            self.assertTrue(json.loads(p.read_text())["checksum"].startswith("sha256:")); s.load()
    def test_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; s=InstitutionalMemoryStore(p); s.save(InstitutionalMemory())
            raw=json.loads(p.read_text()); raw["health"]["tampered"]={"status":"COMPLETED","latency_ms":1}
            p.write_text(json.dumps(raw))
            with self.assertRaises(ValueError): s.load()
if __name__=="__main__": unittest.main()
