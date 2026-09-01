import json
import unittest

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError
from foundation.tender_radar import (
    DISCOVERY_POLICY as UK_DISCOVERY_POLICY,
    FEED_URL as UK_FEED_URL,
    MOUTH_ID as UK_MOUTH_ID,
    parse_items as uk_parse_items,
)
from foundation.tender_sources import (
    SOURCES,
    UNREGISTERED_CANDIDATES,
    TenderSource,
    UnknownSourceError,
    get_source,
    list_sources,
    parse_source,
)

# A small, REDACTED real-shaped OCDS release package — trimmed from the
# genuine shape tender_radar.py's own docstring documents having pulled
# live from Contracts Finder on 2026-09-01 (buyer/title/amount fields
# replaced with placeholder text; the structural shape — 'releases',
# 'tag', 'ocid', 'tender.status'/'title'/'value'/'tenderPeriod',
# 'buyer.name' — is the real, unaltered OCDS release shape this API
# returns, not invented).
REDACTED_UK_SAMPLE = json.dumps({
    "releases": [
        {
            "ocid": "ocds-b5fd17-000001",
            "tag": ["tender"],
            "date": "2026-08-20T00:00:00Z",
            "tender": {
                "id": "T-000001",
                "title": "REDACTED — winter gritting services",
                "description": "REDACTED — routine gritting contract",
                "status": "active",
                "value": {"amount": 45000, "currency": "GBP"},
                "tenderPeriod": {"endDate": "2026-09-30T00:00:00Z"},
            },
            "buyer": {"name": "REDACTED Council"},
        },
        {
            # award release — must be excluded, same as tender_radar's
            # own OPEN_TAG discipline
            "ocid": "ocds-b5fd17-000002",
            "tag": ["award"],
            "tender": {"id": "T-000002", "status": "complete"},
        },
    ],
}).encode("utf-8")


class TestGetSource(unittest.TestCase):
    def test_known_source_returns_TenderSource(self):
        source = get_source(UK_MOUTH_ID)
        self.assertIsInstance(source, TenderSource)
        self.assertEqual(source.source_id, UK_MOUTH_ID)

    def test_unknown_source_raises_UnknownSourceError(self):
        with self.assertRaises(UnknownSourceError):
            get_source("not_a_real_source_id")

    def test_unknown_source_error_names_registered_sources(self):
        with self.assertRaises(UnknownSourceError) as ctx:
            get_source("nope")
        self.assertIn(UK_MOUTH_ID, str(ctx.exception))


class TestUnverifiedCandidatesAreNeverRegistered(unittest.TestCase):
    """The hard honesty rule this module's docstring states: a source
    verified live but declined for a stated reason (TED's POST-only API,
    Prozorro's wrong-shape changefeed, robots-disallowed hosts, ...)
    must be exactly as unreachable through get_source()/parse_source()
    as a source never investigated at all."""

    def test_every_unregistered_candidate_id_is_absent_from_SOURCES(self):
        for candidate_id in UNREGISTERED_CANDIDATES:
            self.assertNotIn(candidate_id, SOURCES)

    def test_every_unregistered_candidate_raises_on_get_source(self):
        for candidate_id in UNREGISTERED_CANDIDATES:
            with self.assertRaises(UnknownSourceError):
                get_source(candidate_id)

    def test_every_unregistered_candidate_raises_on_parse_source(self):
        for candidate_id in UNREGISTERED_CANDIDATES:
            with self.assertRaises(UnknownSourceError):
                parse_source(candidate_id, b"{}")

    def test_unregistered_candidates_have_a_stated_reason(self):
        for candidate_id, reason in UNREGISTERED_CANDIDATES.items():
            self.assertIsInstance(reason, str)
            self.assertTrue(reason.strip(), f"{candidate_id} has an empty reason")


class TestListSources(unittest.TestCase):
    def test_contains_exactly_the_registered_uk_source(self):
        self.assertEqual(list_sources(), (UK_MOUTH_ID,))

    def test_is_sorted_and_a_tuple(self):
        sources = list_sources()
        self.assertIsInstance(sources, tuple)
        self.assertEqual(sources, tuple(sorted(sources)))


class TestUKSourceReusesTenderRadarRatherThanDuplicating(unittest.TestCase):
    """Not a re-implementation: the registered entry must be the exact
    same objective/URL/parser tender_radar.py itself already uses and
    has already verified live — proving reuse, not a second copy that
    could silently drift from the original."""

    def test_feed_url_is_the_real_tender_radar_feed_url(self):
        self.assertEqual(SOURCES[UK_MOUTH_ID].feed_url, UK_FEED_URL)

    def test_discovery_policy_is_the_real_tender_radar_policy_object(self):
        self.assertIs(SOURCES[UK_MOUTH_ID].discovery_policy, UK_DISCOVERY_POLICY)
        self.assertIsInstance(SOURCES[UK_MOUTH_ID].discovery_policy, DiscoveryPolicy)

    def test_parser_is_the_real_tender_radar_parse_items_function(self):
        self.assertIs(SOURCES[UK_MOUTH_ID].parser, uk_parse_items)


class TestParseSourceNormalisesTheRealPayloadShape(unittest.TestCase):
    def test_open_tender_is_normalised_into_the_common_item_shape(self):
        items = parse_source(UK_MOUTH_ID, REDACTED_UK_SAMPLE)
        self.assertEqual(len(items), 1, "the award-tagged release must be excluded")
        item = items[0]
        self.assertEqual(item["key"], "ocds-b5fd17-000001")
        self.assertEqual(item["ocid"], "ocds-b5fd17-000001")
        self.assertEqual(item["status"], "active")
        self.assertEqual(item["amount"], 45000)
        self.assertEqual(item["currency"], "GBP")
        self.assertEqual(item["buyer_name"], "REDACTED Council")
        self.assertIn("title", item)
        self.assertIn("deadline", item)
        self.assertIn("published", item)

    def test_matches_calling_tender_radar_parse_items_directly(self):
        """The registry's normalised output must be identical to calling
        tender_radar.parse_items() directly on the same bytes — proof
        the registry adds no second, silently-diverging parse path."""
        self.assertEqual(
            parse_source(UK_MOUTH_ID, REDACTED_UK_SAMPLE),
            uk_parse_items(REDACTED_UK_SAMPLE),
        )


class TestMalformedPayloadIsAStructuredRefusalNotACrash(unittest.TestCase):
    def test_non_json_bytes_raise_FetchError(self):
        with self.assertRaises(FetchError):
            parse_source(UK_MOUTH_ID, b"not json at all {{{")

    def test_json_root_that_is_not_an_object_raises_FetchError(self):
        with self.assertRaises(FetchError):
            parse_source(UK_MOUTH_ID, b"[1, 2, 3]")

    def test_missing_releases_array_raises_FetchError(self):
        with self.assertRaises(FetchError):
            parse_source(UK_MOUTH_ID, b'{"not_releases": []}')

    def test_empty_bytes_raise_FetchError_not_crash(self):
        with self.assertRaises(FetchError):
            parse_source(UK_MOUTH_ID, b"")


class TestWrongTypedFieldsDoNotCrash(unittest.TestCase):
    def test_a_release_that_is_not_a_dict_is_skipped(self):
        raw = json.dumps({"releases": ["not-a-dict", 42, None]}).encode()
        self.assertEqual(parse_source(UK_MOUTH_ID, raw), ())

    def test_wrong_typed_tender_value_amount_does_not_crash(self):
        raw = json.dumps({
            "releases": [{
                "ocid": "ocds-b5fd17-000003",
                "tag": ["tender"],
                "tender": {
                    "id": "T-000003",
                    "status": "active",
                    "value": {"amount": "not-a-number", "currency": 12345},
                },
                "buyer": {"name": ["not", "a", "string"]},
            }],
        }).encode()
        items = parse_source(UK_MOUTH_ID, raw)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIsNone(item["amount"])
        self.assertEqual(item["currency"], "")
        self.assertEqual(item["buyer_name"], "")

    def test_a_release_missing_ocid_is_dropped_not_crashed(self):
        raw = json.dumps({
            "releases": [{
                "tag": ["tender"],
                "tender": {"id": "T-no-ocid", "status": "active"},
            }],
        }).encode()
        self.assertEqual(parse_source(UK_MOUTH_ID, raw), ())


class TestSourceRegistryEntryFields(unittest.TestCase):
    def test_registered_entry_declares_a_real_licence(self):
        source = SOURCES[UK_MOUTH_ID]
        self.assertTrue(source.licence.strip())
        self.assertTrue(source.licence_note.strip())

    def test_registered_entry_declares_a_payload_shape(self):
        self.assertTrue(SOURCES[UK_MOUTH_ID].payload_shape.strip())

    def test_registered_entry_declares_verification_provenance(self):
        source = SOURCES[UK_MOUTH_ID]
        self.assertTrue(source.verified_at.strip())
        self.assertTrue(source.verified_note.strip())


if __name__ == "__main__":
    unittest.main()
