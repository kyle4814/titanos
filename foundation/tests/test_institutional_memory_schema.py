import json,tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import CURRENT_SCHEMA,InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt
class TestInstitutionalMemorySchema(unittest.TestCase):
    def test_new_writes_include_schema(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; s=InstitutionalMemoryStore(p); m=InstitutionalMemory()
            # Writes have required a learning receipt since 1c90bb98; this test predates that.
            s.save(m,LearningReceipt.create("test","seed",(),s._raw_payload(),s._payload(m)))
            self.assertEqual(json.loads(p.read_text())["schema_version"],CURRENT_SCHEMA)
    def test_v1_migrates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; p.write_text(json.dumps({"opportunities":{},"health":{},"specialization":[]}))
            out=InstitutionalMemoryStore(p).load()
            self.assertEqual(out.opportunity_learning.records,{})
    def test_future_schema_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; p.write_text(json.dumps({"schema_version":999}))
            with self.assertRaises(ValueError): InstitutionalMemoryStore(p).load()
if __name__=="__main__": unittest.main()
