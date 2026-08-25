"""Tests for taal/integrator/integrator.py."""

from __future__ import annotations

import re
import unittest

from taal.integrator.integrator import (
    RawSignal, NormalizedEvent, THREAT_CLASSES,
    normalize, propose_archetype_candidates,
)

# Conclusory words that must never appear in what this module returns or
# would log. Deliberately checked against the actual string content, not
# asserted-and-trusted.
_CONCLUSORY_WORDS = ("detected", "confirmed", "malicious", "attack")


class TestNormalizePreservesRawFacts(unittest.TestCase):
    def test_all_raw_facts_present_verbatim_and_in_order(self):
        facts = (
            "3 failed logins in 10s",
            "login attempted from new geolocation",
            "user agent changed mid-session",
        )
        signal = RawSignal(
            signal_id="sig-1",
            source_type="ACCESS_REQUEST",
            entity="user:alice",
            observed_action="repeated login attempts",
            affected_resource="auth-service",
            raw_facts=facts,
        )
        event = normalize(signal)
        self.assertEqual(event.signals, facts)
        self.assertEqual(len(event.signals), len(facts))

    def test_empty_raw_facts_produces_empty_signals_not_an_error(self):
        signal = RawSignal(
            signal_id="sig-2",
            source_type="AUDIT_LOG",
            entity="svc:billing",
            observed_action="routine health check",
            affected_resource="billing-db",
            raw_facts=(),
        )
        event = normalize(signal)
        self.assertEqual(event.signals, ())

    def test_normalize_maps_core_fields(self):
        signal = RawSignal(
            signal_id="sig-3",
            source_type="AI_TOOL_REQUEST",
            entity="agent:build-bot",
            observed_action="requested sudo",
            affected_resource="ci-runner-7",
            raw_facts=("sudo requested outside allowed window",),
            timestamp="2026-08-25T00:00:00Z",
        )
        event = normalize(signal)
        self.assertEqual(event.event_id, "sig-3")
        self.assertEqual(event.source_type, "AI_TOOL_REQUEST")
        self.assertEqual(event.entity, "agent:build-bot")
        self.assertEqual(event.action, "requested sudo")
        self.assertEqual(event.resource, "ci-runner-7")
        self.assertEqual(event.original_timestamp, "2026-08-25T00:00:00Z")
        self.assertTrue(event.normalized_at)  # populated, non-empty


class TestProposeArchetypeCandidates(unittest.TestCase):
    def test_privilege_escalation_keywords_produce_candidate(self):
        event = NormalizedEvent(
            event_id="e1", source_type="AI_TOOL_REQUEST", entity="agent:x",
            action="requested privilege escalation via sudo",
            resource="prod-db",
            signals=("sudo requested",),
        )
        candidates = propose_archetype_candidates(event)
        self.assertIn("PRIVILEGE_ESCALATION_ATTEMPTS", candidates)

    def test_multiple_keyword_hits_produce_multiple_candidates(self):
        event = NormalizedEvent(
            event_id="e2", source_type="SECURITY_TELEMETRY", entity="host:9",
            action="attempted remote code execution after privilege escalation",
            resource="prod-cluster",
            signals=("arbitrary code executed", "sudo requested"),
        )
        candidates = propose_archetype_candidates(event)
        self.assertIn("UNAUTHORIZED_EXECUTION", candidates)
        self.assertIn("PRIVILEGE_ESCALATION_ATTEMPTS", candidates)
        self.assertGreaterEqual(len(candidates), 2)

    def test_all_returned_candidates_are_from_the_closed_set(self):
        event = NormalizedEvent(
            event_id="e3", source_type="POLICY_VIOLATION", entity="user:bob",
            action="exfiltrated data via bulk download after impersonating admin",
            resource="s3-bucket",
            signals=("large outbound transfer observed", "spoofed identity header"),
        )
        candidates = propose_archetype_candidates(event)
        for c in candidates:
            self.assertIn(c, THREAT_CLASSES)

    def test_benign_signal_produces_empty_tuple(self):
        """No candidate archetype fits a mundane, benign signal.

        An empty tuple is a legitimate, valid output — not an error.
        """
        event = NormalizedEvent(
            event_id="e4", source_type="APPLICATION_EVENT", entity="user:carol",
            action="viewed her own profile page",
            resource="profile-service",
            signals=("normal page view", "response time 42ms"),
        )
        candidates = propose_archetype_candidates(event)
        self.assertEqual(candidates, ())

    def test_output_is_sorted_and_deterministic(self):
        event = NormalizedEvent(
            event_id="e5", source_type="ANOMALY", entity="agent:y",
            action="jailbreak attempt via prompt injection and phishing pretext",
            resource="chat-agent",
            signals=("ignore previous instructions detected in payload",),
        )
        first = propose_archetype_candidates(event)
        second = propose_archetype_candidates(event)
        self.assertEqual(first, second)
        self.assertEqual(first, tuple(sorted(first)))


class TestNeverConclusory(unittest.TestCase):
    """The integrator proposes candidates, plural — never a conclusion.

    Directive §9: "The integrator must never claim 'attack detected'
    without preserving the signals supporting that conclusion." This
    module goes further and never uses conclusory language at all. This
    test greps the ACTUAL returned string content (not the source code)
    across a battery of signals designed to maximize keyword hits, and
    asserts none of the conclusory words ever appear in a candidate label.
    """

    def test_no_conclusory_words_in_any_candidate_across_battery(self):
        battery = [
            ("impersonated the CEO via spoofed email and forged credential",
             "identity-service",
             ("spoofing detected by upstream tool",)),
            ("attempted privilege escalation, sudo, root access grab",
             "prod-host",
             ("elevate to root observed",)),
            ("exfiltrated data via bulk download, large outbound transfer",
             "data-warehouse",
             ("checksum mismatch also noted", "tamper suspected")),
            ("arbitrary code execution, remote code execution attempt",
             "worker-node",
             ("unauthorized execution logged",)),
            ("insider disgruntled employee cleared audit trail",
             "hr-system",
             ("log tampering", "disabled logging")),
            ("denial of service causing service unavailable outage caused by flood",
             "edge-lb",
             ("resource exhaustion", "excessive requests")),
            ("cross-tenant trust boundary violation via third-party delegation",
             "multi-tenant-api",
             ("delegated to external subcontractor access",)),
        ]
        for action, resource, facts in battery:
            event = NormalizedEvent(
                event_id="batch", source_type="SECURITY_TELEMETRY",
                entity="entity:x", action=action, resource=resource,
                signals=facts,
            )
            candidates = propose_archetype_candidates(event)
            joined = " ".join(candidates).lower()
            for word in _CONCLUSORY_WORDS:
                self.assertNotIn(
                    word, joined,
                    msg=(
                        f"conclusory word '{word}' leaked into candidate "
                        f"output {candidates!r} for action={action!r}"
                    ),
                )
            # Category names themselves (e.g. containing "ATTEMPTS") are
            # fine — they are classification labels, not claims. Only the
            # exact conclusory words above are forbidden, and none of the
            # THREAT_CLASSES enum values contain them.
            for c in candidates:
                self.assertNotRegex(c, re.compile("|".join(_CONCLUSORY_WORDS), re.I))

    def test_threat_classes_enum_itself_contains_no_conclusory_word(self):
        for cls in THREAT_CLASSES:
            lowered = cls.lower()
            for word in _CONCLUSORY_WORDS:
                self.assertNotIn(word, lowered)


if __name__ == "__main__":
    unittest.main()
