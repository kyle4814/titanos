import unittest
from foundation.specialization import SpecializationBook
class TestSpecialization(unittest.TestCase):
    def test_domain_success_routing(self):
        b=SpecializationBook(); b.record("a","security",completed=True,evidence_count=5); b.record("b","security",completed=False)
        self.assertEqual(b.rank(("b","a"),"security"),("a","b"))
if __name__=="__main__": unittest.main()
