import unittest

from claim_ledger import Claim, ClaimError, Ledger


class TestClaimValidation(unittest.TestCase):
    def test_verified_fact_requires_source(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "text", "VERIFIED_FACT", "HIGH", source="")

    def test_verified_fact_with_source_ok(self):
        c = Claim("c1", "text", "VERIFIED_FACT", "HIGH", source="http://x")
        self.assertEqual(c.classification, "VERIFIED_FACT")

    def test_opinion_cannot_be_high_confidence(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "text", "OPINION_OR_TREND", "HIGH")

    def test_unverified_cannot_be_high_confidence(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "text", "UNVERIFIED_CLAIM", "HIGH")

    def test_opinion_at_low_confidence_ok(self):
        c = Claim("c1", "text", "OPINION_OR_TREND", "LOW")
        self.assertEqual(c.confidence, "LOW")

    def test_bad_classification_rejected(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "text", "TOTALLY_MADE_UP", "LOW")

    def test_bad_confidence_rejected(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "text", "OPINION_OR_TREND", "SUPER_HIGH")

    def test_empty_text_rejected(self):
        with self.assertRaises(ClaimError):
            Claim("c1", "  ", "OPINION_OR_TREND", "LOW")

    def test_empty_claim_id_rejected(self):
        with self.assertRaises(ClaimError):
            Claim("  ", "text", "OPINION_OR_TREND", "LOW")


class TestLedger(unittest.TestCase):
    def test_by_tier_groups_correctly(self):
        ledger = Ledger()
        ledger.add(Claim("c1", "a fact", "VERIFIED_FACT", "HIGH", source="s"))
        ledger.add(Claim("c2", "an opinion", "OPINION_OR_TREND", "LOW"))
        tiers = ledger.by_tier()
        self.assertEqual(len(tiers["VERIFIED_FACT"]), 1)
        self.assertEqual(len(tiers["OPINION_OR_TREND"]), 1)
        self.assertEqual(len(tiers["UNVERIFIED_CLAIM"]), 0)

    def test_no_conflict_without_shared_subject(self):
        ledger = Ledger()
        ledger.add(Claim("c1", "a", "VERIFIED_FACT", "HIGH", source="s"))
        ledger.add(Claim("c2", "b", "OPINION_OR_TREND", "LOW"))
        self.assertEqual(ledger.find_subject_conflicts(), [])

    def test_conflict_detected_across_tiers_same_subject(self):
        ledger = Ledger()
        ledger.add(Claim("c1", "a", "VERIFIED_FACT", "HIGH", source="s", subject="X"))
        ledger.add(Claim("c2", "b", "OPINION_OR_TREND", "LOW", subject="X"))
        conflicts = ledger.find_subject_conflicts()
        self.assertEqual(len(conflicts), 1)
        subject, group = conflicts[0]
        self.assertEqual(subject, "X")
        self.assertEqual(len(group), 2)

    def test_no_conflict_same_subject_same_tier(self):
        ledger = Ledger()
        ledger.add(Claim("c1", "a", "VERIFIED_FACT", "HIGH", source="s", subject="X"))
        ledger.add(Claim("c2", "b", "VERIFIED_FACT", "MEDIUM", source="s2", subject="X"))
        self.assertEqual(ledger.find_subject_conflicts(), [])

    def test_subjectless_claims_never_conflict(self):
        ledger = Ledger()
        ledger.add(Claim("c1", "a", "VERIFIED_FACT", "HIGH", source="s"))
        ledger.add(Claim("c2", "b", "OPINION_OR_TREND", "LOW"))
        ledger.add(Claim("c3", "c", "UNVERIFIED_CLAIM", "LOW"))
        self.assertEqual(ledger.find_subject_conflicts(), [])


if __name__ == "__main__":
    unittest.main()
