import json,tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt
def _seed(s):
    # Writes have required a learning receipt since 1c90bb98; these tests predate that.
    m=InstitutionalMemory(); s.save(m,LearningReceipt.create("test","seed",(),s._raw_payload(),s._payload(m)))
class TestInstitutionalMemoryIntegrity(unittest.TestCase):
    def test_checksum_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; s=InstitutionalMemoryStore(p); _seed(s)
            self.assertTrue(json.loads(p.read_text())["checksum"].startswith("sha256:")); s.load()
    def test_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; s=InstitutionalMemoryStore(p); _seed(s)
            raw=json.loads(p.read_text()); raw["health"]["tampered"]={"status":"COMPLETED","latency_ms":1}
            p.write_text(json.dumps(raw))
            with self.assertRaises(ValueError): s.load()
if __name__=="__main__": unittest.main()
