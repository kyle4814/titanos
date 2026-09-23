"""Regression tests for evidence -> operator-digest projection."""

import unittest
from datetime import datetime, timezone

from foundation.ops_digest import opportunities_from_locked_entries
from foundation.signal_spine import (
    CanonicalSignal,
    raw_value_map_entry,
    fuse,
    target_lock,
)


NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def _signal(signal_id, kind, claim, source_id):
    return CanonicalSignal(
        signal_id=signal_id,
        source_id=source_id,
        source_type="OFFICIAL",
        source_ref=f"https://example.test/{signal_id}",
        target="target-a",
        kind=kind,
        claim=claim,
        observed_at=NOW.isoformat(),
        event_at=NOW.isoformat(),
        source_lineage=signal_id,
        target_established_by="SOURCE_NATIVE",
        facts={"state": kind},
        pressure_class="EXPLICIT_DEMAND" if kind == "DEMAND" else "NONE",
        pressure_evidence="documented demand" if kind == "DEMAND" else "",
    )


class TestEvidenceToDigestProjection(unittest.TestCase):
    def test_locked_entry_produces_one_conservative_card(self):
        signals = (
            _signal("s-demand", "DEMAND", "Customer requests this capability", "a"),
            _signal("s-release", "RELEASE", "Official release establishes the target", "b"),
        )
        fused = fuse(signals, now=NOW)
        entry = raw_value_map_entry(
            fused,
            why_on_the_map=("independent demand and release evidence",),
            what_would_kill_it="source evidence is withdrawn",
            next_cheapest_experiment="Open both primary sources and verify scope.",
            now=NOW,
        )
        lock = target_lock(entry)
        self.assertEqual(lock.state, "LOCKED")

        cards = opportunities_from_locked_entries(((entry, lock),))

        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card.status, "PURSUE")
        self.assertEqual(card.value, "UNKNOWN — no money observed in qualifying evidence")
        self.assertIn("commercial value not observed", card.note)
        self.assertIn("signal_spine::s-demand", card.source_ref)

    def test_non_locked_entry_never_becomes_a_card(self):
        signal = _signal("s-only", "DEMAND", "One observation only", "a")
        fused = fuse((signal,), now=NOW)
        entry = raw_value_map_entry(
            fused,
            why_on_the_map=("single observation",),
            what_would_kill_it="independent evidence contradicts it",
            next_cheapest_experiment="Find an independent source.",
            now=NOW,
        )
        lock = target_lock(entry)

        self.assertNotEqual(lock.state, "LOCKED")
        self.assertEqual(opportunities_from_locked_entries(((entry, lock),)), ())

    def test_disqualified_locked_shape_never_becomes_a_card(self):
        signals = (
            _signal("s-demand", "DEMAND", "Demand exists", "a"),
            _signal("s-release", "RELEASE", "Release exists", "b"),
        )
        fused = fuse(signals, now=NOW)
        entry = raw_value_map_entry(
            fused,
            why_on_the_map=("two independent observations",),
            what_would_kill_it="disqualifier",
            next_cheapest_experiment="Check the disqualifier.",
            disqualifiers=("OUT_OF_SCOPE",),
            now=NOW,
        )
        lock = target_lock(entry)

        self.assertEqual(lock.state, "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(opportunities_from_locked_entries(((entry, lock),)), ())


if __name__ == "__main__":
    unittest.main()
