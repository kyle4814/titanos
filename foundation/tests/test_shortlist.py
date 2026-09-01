import unittest
from datetime import datetime, timezone

from foundation import shortlist
from foundation.relevance import CapabilityProfile
from foundation.signal_spine import CanonicalSignal


def _signal(signal_id, claim, buyer_safe="", title_safe="", deadline="",
            source_id="tender_radar_eu_ted", source_ref="https://example/query",
            tender_id="", ocid="", extra_facts=None, extra_evidence=None):
    facts = {"deadline": deadline}
    if extra_facts:
        facts.update(extra_facts)
    evidence = {
        "buyer_name_safe": buyer_safe,
        "title_safe": title_safe,
        "deadline": deadline,
        "tender_id": tender_id,
        "ocid": ocid,
    }
    if extra_evidence:
        evidence.update(extra_evidence)
    return CanonicalSignal(
        signal_id=signal_id,
        source_id=source_id,
        source_type="OFFICIAL",
        source_ref=source_ref,
        target=buyer_safe or signal_id,
        kind="DEMAND",
        claim=claim,
        observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        target_established_by="SOURCE_NATIVE",
        facts=facts,
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence="a public notice stating intent to purchase",
    )


PROFILE = CapabilityProfile(
    name="cyber-security-operator",
    declared_by="test",
    keywords=frozenset({
        "cyber security", "penetration testing", "security audit",
        "incident response", "soc",
    }),
    exclusions=frozenset({"construction", "catering"}),
)


class BuildShortlistTests(unittest.TestCase):
    def test_deterministic_ordering_across_repeated_calls(self):
        signals = [
            _signal("s1", "open tender: cyber security penetration testing "
                          "security audit services", buyer_safe="Buyer A",
                    title_safe="Cyber security consulting"),
            _signal("s2", "open tender: incident response soc security "
                          "audit services", buyer_safe="Buyer B",
                    title_safe="SOC services"),
            _signal("s3", "open tender: construction of a new building",
                    buyer_safe="Buyer C", title_safe="Construction works"),
        ]
        first = shortlist.build_shortlist(signals, PROFILE)
        second = shortlist.build_shortlist(signals, PROFILE)
        self.assertEqual(
            [e.signal_id for e in first], [e.signal_id for e in second])
        self.assertEqual(first, second)

    def test_missing_deadline_renders_unknown_not_blank_or_guess(self):
        signals = [
            _signal("s1", "open tender: cyber security penetration testing "
                          "security audit", buyer_safe="Buyer A",
                    title_safe="Security services", deadline=""),
        ]
        entries = shortlist.build_shortlist(signals, PROFILE)
        self.assertEqual(entries[0].deadline, shortlist.UNKNOWN)
        digest = shortlist.render_digest(entries)
        self.assertIn(f"deadline: {shortlist.UNKNOWN}", digest)
        self.assertNotIn("deadline: \n", digest)

    def test_empty_input_is_valid_empty_digest_not_an_error(self):
        entries = shortlist.build_shortlist([], PROFILE)
        self.assertEqual(entries, ())
        digest = shortlist.render_digest(entries)
        self.assertIsInstance(digest, str)
        self.assertIn("valid, honest outcome", digest)

    def test_digest_never_contains_qualified(self):
        signals = [
            _signal("s1", "open tender: cyber security penetration testing "
                          "security audit", buyer_safe="Buyer A",
                    title_safe="Security services", deadline="2026-10-01"),
            _signal("s2", "open tender: construction works",
                    buyer_safe="Buyer B", title_safe="Construction"),
        ]
        entries = shortlist.build_shortlist(signals, PROFILE)
        digest = shortlist.render_digest(entries)
        self.assertNotIn("qualified", digest.lower())
        for entry in entries:
            self.assertNotIn("qualified", entry.note.lower())

    def test_hostile_notice_text_is_neutralised(self):
        hostile_buyer = "Buyer\x1b[31mRED\x1b[0m\nSecond line"
        hostile_title = "A" * 5000
        signals = [
            _signal("s1", "open tender: cyber security penetration testing "
                          "security audit", buyer_safe=hostile_buyer,
                    title_safe=hostile_title, deadline="2026-10-01"),
        ]
        entries = shortlist.build_shortlist(signals, PROFILE)
        digest = shortlist.render_digest(entries)
        self.assertNotIn("\x1b", digest)
        self.assertNotIn("\n\nSecond line", digest)
        # No single rendered line should balloon to the raw hostile length.
        for line in digest.splitlines():
            self.assertLess(len(line), 1000)

    def test_excluded_entry_can_never_outrank_strong_match(self):
        signals = [
            _signal("s1", "open tender: construction of a building, "
                          "catering services included",
                    buyer_safe="Buyer EXCLUDED", title_safe="Construction"),
            _signal("s2", "open tender: cyber security penetration testing "
                          "security audit incident response services",
                    buyer_safe="Buyer STRONG", title_safe="Security services"),
        ]
        entries = shortlist.build_shortlist(signals, PROFILE)
        bands = [e.band for e in entries]
        self.assertIn("EXCLUDED", bands)
        self.assertIn("STRONG_MATCH", bands)
        self.assertLess(bands.index("STRONG_MATCH"), bands.index("EXCLUDED"))

    def test_limit_truncates_but_preserves_order(self):
        signals = [
            _signal(f"s{i}", "open tender: cyber security penetration "
                              "testing security audit incident response",
                    buyer_safe=f"Buyer {i}", title_safe="Security services")
            for i in range(5)
        ]
        full = shortlist.build_shortlist(signals, PROFILE)
        limited = shortlist.build_shortlist(signals, PROFILE, limit=2)
        self.assertEqual(len(limited), 2)
        self.assertEqual(limited, full[:2])

    def test_header_always_states_what_these_are_and_are_not(self):
        digest = shortlist.render_digest(())
        self.assertIn("NOT LEADS", digest)
        self.assertIn("NOT REVENUE", digest)


if __name__ == "__main__":
    unittest.main()
