"""Tests for `foundation/sources.py` and `foundation.hunt.hunt_multi()`.

Offline throughout -- every `Source` here is built with an injected
`fetch_items` lambda; no test opens a socket. This file is the proof
for the module's own CRITICAL HONESTY RULE: a criteria-less source can
only ever produce `INSUFFICIENT_DATA`.
"""

import unittest

from foundation.hunt import BAND_ORDER, HuntIntegrityError, hunt_multi
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile
from foundation.sources import (
    NZ_GETS,
    Source,
    TED,
    UK_CONTRACTS_FINDER,
    normalise_gets_nz,
    normalise_ted,
    normalise_tenderned_nl,
    normalise_udbud_dk,
    normalise_uk_contracts_finder,
    sources_for_query,
    _ted_signal_from_raw,
)

SOLO = OperatorProfile(
    name="solo operator (AU)",
    staff_count=1,
    certifications=frozenset(),
    insurance_cover_eur=None,
    corporate_references=(),
    languages=frozenset({"ENG"}),
)


def degewo_notice():
    """Real TED shape with real blocking clauses (578580-2026)."""
    return {
        "publication-number": "578580-2026",
        "notice-title": {"eng": ["Framework: penetration testing"]},
        "buyer-name": {"deu": ["degewo AG"]},
        "procedure-type": ["open"],
        "submission-language": ["DEU"],
        "selection-criterion-lot": [
            "slc-suit-reg-prof", "slc-stand-other",
            "slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp",
        ],
        "selection-criterion-description-lot": {
            "deu": [
                "Der Anbieter hat mindestens zwei (2) vergleichbare "
                "Referenzen aus den letzten fuenf (5) Jahren nachzuweisen."
            ]
        },
    }


def gets_item(key="gets-1", title="Penetration testing services",
              description="A cyber security tender.", organisation="MFAT",
              link="https://www.gets.govt.nz/ExternalTenderShortDetails.htm?id=1"):
    return {
        "key": key, "guid": key, "link": link, "title": title,
        "description": description, "organisation": organisation,
        "close_date": "1 Oct 2026", "rfx_id": "RFX-1",
        "published": "2026-09-01", "categories": ("cyber security",),
    }


def uk_item(key="ocds-1", release_id="rel-1", title="Cyber security audit",
            description="Penetration testing engagement.",
            buyer_name="Home Office"):
    return {
        "key": key, "ocid": key, "tender_id": "t-1", "release_id": release_id,
        "title": title, "description": description, "status": "active",
        "amount": 50000, "currency": "GBP", "value_detail": "50000 GBP",
        "deadline": "2026-10-01T00:00:00Z", "buyer_name": buyer_name,
        "cpv": "72000000", "published": "2026-09-01",
    }


class TestNormaliseTed(unittest.TestCase):
    def test_passes_through_a_valid_notice(self):
        n = normalise_ted(degewo_notice())
        self.assertEqual(n["publication-number"], "578580-2026")
        self.assertIn("selection-criterion-lot", n)

    def test_declines_a_notice_with_no_publication_number(self):
        self.assertIsNone(normalise_ted({"notice-title": {"eng": ["x"]}}))


class TestNormaliseGetsNz(unittest.TestCase):
    def test_builds_a_ted_shaped_dict(self):
        n = normalise_gets_nz(gets_item())
        self.assertEqual(n["publication-number"], "gets-1")
        self.assertEqual(n["notice-title"], {"eng": ("Penetration testing services",)})
        self.assertEqual(n["buyer-name"], {"eng": ("MFAT",)})

    def test_declines_an_item_with_no_identity(self):
        self.assertIsNone(normalise_gets_nz({"title": "x"}))

    def test_never_sets_any_criteria_field(self):
        n = normalise_gets_nz(gets_item())
        forbidden = (
            "selection-criterion-lot", "selection-criterion-description-lot",
            "selection-criteria-source", "exclusion-grounds",
            "exclusion-grounds-description", "exclusion-grounds-source-proc",
            "tenderer-legal-form-lot", "tenderer-legal-form-description-lot",
            "subcontracting-allowed-lot", "subcontracting-obligation-lot",
            "subcontracting-percentage", "subcontracting-description",
            "variant-allowed-lot", "tender-variant", "submission-language",
        )
        for field in forbidden:
            self.assertNotIn(field, n, f"{field} must never be fabricated")


class TestNormaliseUkContractsFinder(unittest.TestCase):
    def test_builds_a_ted_shaped_dict(self):
        n = normalise_uk_contracts_finder(uk_item())
        self.assertEqual(n["publication-number"], "rel-1")
        self.assertEqual(n["buyer-name"], {"eng": ("Home Office",)})
        self.assertIn("links", n)

    def test_falls_back_to_ocid_when_release_id_missing(self):
        item = uk_item(release_id="")
        n = normalise_uk_contracts_finder(item)
        self.assertEqual(n["publication-number"], "ocds-1")

    def test_declines_an_item_with_no_identity(self):
        self.assertIsNone(normalise_uk_contracts_finder({"title": "x"}))

    def test_never_sets_any_criteria_field(self):
        n = normalise_uk_contracts_finder(uk_item())
        forbidden = (
            "selection-criterion-lot", "selection-criterion-description-lot",
            "selection-criteria-source", "exclusion-grounds",
            "exclusion-grounds-description", "exclusion-grounds-source-proc",
            "tenderer-legal-form-lot", "tenderer-legal-form-description-lot",
            "subcontracting-allowed-lot", "subcontracting-obligation-lot",
            "subcontracting-percentage", "subcontracting-description",
            "variant-allowed-lot", "tender-variant", "submission-language",
        )
        for field in forbidden:
            self.assertNotIn(field, n, f"{field} must never be fabricated")


CRITERIA_FIELDS = (
    "selection-criterion-lot", "selection-criterion-description-lot",
    "selection-criteria-source", "exclusion-grounds",
    "exclusion-grounds-description", "exclusion-grounds-source-proc",
    "tenderer-legal-form-lot", "tenderer-legal-form-description-lot",
    "subcontracting-allowed-lot", "subcontracting-obligation-lot",
    "subcontracting-percentage", "subcontracting-description",
    "variant-allowed-lot", "tender-variant", "submission-language",
)


def dk_item(key="dk-1", title="Cybersecurity advisory framework",
            description="Rammeaftale om cybersikkerhed.",
            buyer="Danmarks Nationalbank"):
    """`mouth_udbud_dk.parse_items()`'s own output shape -- `buyer`,
    not `organisation`, and NO link field at all."""
    return {
        "key": key, "notice_id": key, "notice_publication_number": "2026/S 1",
        "title": title, "description": description, "buyer": buyer,
        "cpv_title": "IT services", "published": "2026-09-01",
        "deadline": "2026-10-02T12:00:00", "value": "9200000",
        "value_currency": "DKK", "notice_type": "cn-standard",
    }


def nl_item(key="nl-1", title="SIEM en SOC dienstverlening",
            description="Aanbesteding cyber security.",
            buyer="Veiligheidsregio Haaglanden",
            link="https://www.tenderned.nl/aankondigingen/overzicht/1"):
    return {
        "key": key, "publication_id": key, "title": title,
        "description": description, "buyer": buyer,
        "published": "2026-09-01", "deadline": "2026-09-28T12:00:00+02:00",
        "procedure": "Openbare procedure", "notice_type": "Aankondiging",
        "link": link,
    }


class TestNormaliseUdbudDk(unittest.TestCase):
    """Denmark's feed names the buyer `buyer` and carries no href --
    two shape differences from every source registered before it, and
    both are places a shared normaliser would have silently produced a
    notice with no buyer and no link rather than failing."""

    def test_builds_a_ted_shaped_dict(self):
        n = normalise_udbud_dk(dk_item())
        self.assertEqual(n["publication-number"], "dk-1")
        self.assertEqual(n["buyer-name"], {"eng": ("Danmarks Nationalbank",)})

    def test_the_notice_url_is_derived_from_the_notice_id(self):
        n = normalise_udbud_dk(dk_item(key="f104f4f6"))
        self.assertEqual(n["links"]["html"]["eng"],
                         "https://udbud.dk/bekendtgoerelse/f104f4f6")

    def test_declines_an_item_with_no_identity(self):
        self.assertIsNone(normalise_udbud_dk({"title": "x"}))

    def test_declines_rather_than_building_a_url_from_a_blank_key(self):
        """Without this guard the derived href would be the bare
        `/bekendtgoerelse/` prefix -- a link to nothing, presented as a
        link to the notice."""
        self.assertIsNone(normalise_udbud_dk(dk_item(key="   ")))

    def test_never_sets_any_criteria_field(self):
        n = normalise_udbud_dk(dk_item())
        for field in CRITERIA_FIELDS:
            self.assertNotIn(field, n, f"{field} must never be fabricated")


class TestNormaliseTenderNedNl(unittest.TestCase):
    def test_builds_a_ted_shaped_dict(self):
        n = normalise_tenderned_nl(nl_item())
        self.assertEqual(n["publication-number"], "nl-1")
        self.assertEqual(n["buyer-name"],
                         {"eng": ("Veiligheidsregio Haaglanden",)})
        self.assertIn("links", n)

    def test_a_missing_link_is_omitted_not_invented(self):
        n = normalise_tenderned_nl(nl_item(link=""))
        self.assertNotIn("links", n)

    def test_declines_an_item_with_no_identity(self):
        self.assertIsNone(normalise_tenderned_nl({"title": "x"}))

    def test_never_sets_any_criteria_field(self):
        n = normalise_tenderned_nl(nl_item())
        for field in CRITERIA_FIELDS:
            self.assertNotIn(field, n, f"{field} must never be fabricated")


class TestNordicBeneluxSourcesAreHonestlyDeclared(unittest.TestCase):
    """Both endpoints DO filter server-side -- proven live. Both are
    registered `server_side_filterable=False` anyway, because the mouth
    picks the search term, not the caller. Declaring True would tell
    `hunt_multi()` the results were already narrowed to ITS query and
    suppress the client-side pass, so a hunt for any keyword would
    return the same fixed cybersecurity page unfiltered."""

    def test_dk_is_client_side_filtered(self):
        from foundation.sources import DK_UDBUD
        self.assertFalse(DK_UDBUD.server_side_filterable)
        self.assertEqual(DK_UDBUD.keyword_fields, ("title", "description"))

    def test_nl_is_client_side_filtered(self):
        from foundation.sources import NL_TENDERNED
        self.assertFalse(NL_TENDERNED.server_side_filterable)
        self.assertEqual(NL_TENDERNED.keyword_fields, ("title", "description"))

    def test_neither_can_ever_produce_qualified(self):
        sources = [
            Source(source_id="DK_UDBUD", fetch_items=lambda: [dk_item()],
                   normalise=normalise_udbud_dk, server_side_filterable=False,
                   keyword_fields=("title", "description")),
            Source(source_id="NL_TENDERNED", fetch_items=lambda: [nl_item()],
                   normalise=normalise_tenderned_nl,
                   server_side_filterable=False,
                   keyword_fields=("title", "description")),
        ]
        r = hunt_multi("cyber", SOLO, sources)
        self.assertEqual(r.assessed, 2)
        self.assertEqual({e.band for e in r.entries}, {"INSUFFICIENT_DATA"})
        for entry in r.entries:
            self.assertEqual(entry.blocking_clauses, ())

    def test_a_non_matching_keyword_is_filtered_out_client_side(self):
        """The direct consequence of the False above: the fixture is a
        real security notice, and a hunt for something else must not
        return it."""
        sources = [
            Source(source_id="DK_UDBUD", fetch_items=lambda: [dk_item()],
                   normalise=normalise_udbud_dk, server_side_filterable=False,
                   keyword_fields=("title", "description")),
        ]
        r = hunt_multi("bridge maintenance", SOLO, sources)
        self.assertEqual(r.assessed, 0)


class TestSourceConstruction(unittest.TestCase):
    def test_rejects_empty_source_id(self):
        with self.assertRaises(ValueError):
            Source(source_id="", fetch_items=lambda: [],
                   normalise=lambda i: i, server_side_filterable=True)

    def test_rejects_client_side_filterable_source_with_no_keyword_fields(self):
        with self.assertRaises(ValueError):
            Source(source_id="X", fetch_items=lambda: [],
                   normalise=lambda i: i, server_side_filterable=False)

    def test_rejects_negative_throttle(self):
        with self.assertRaises(ValueError):
            Source(source_id="X", fetch_items=lambda: [], normalise=lambda i: i,
                   server_side_filterable=True, throttle_seconds=-1)

    def test_uk_contracts_finder_is_not_server_side_filterable(self):
        self.assertFalse(UK_CONTRACTS_FINDER.server_side_filterable)
        self.assertIn("title", UK_CONTRACTS_FINDER.keyword_fields)

    def test_uk_contracts_finder_declares_a_throttle(self):
        self.assertGreater(UK_CONTRACTS_FINDER.throttle_seconds, 0)

    def test_nz_gets_is_not_server_side_filterable(self):
        self.assertFalse(NZ_GETS.server_side_filterable)


class TestSourcesForQuery(unittest.TestCase):
    def test_returns_every_registered_source_by_default(self):
        """Was `test_returns_three_sources_by_default` and hard-coded
        three ids. Two more sources were added to ALL_SOURCES on
        2026-09-02 and this test kept passing -- because it asserted a
        frozen list rather than agreement with the registry, it could
        not notice that the factory had fallen behind. Now it compares
        against ALL_SOURCES, so the same drift fails loudly."""
        from foundation.sources import ALL_SOURCES
        srcs = sources_for_query("cyber security")
        self.assertEqual({s.source_id for s in srcs},
                          {s.source_id for s in ALL_SOURCES})

    def test_include_narrows_the_set(self):
        srcs = sources_for_query("cyber security", include=("NZ_GETS",))
        self.assertEqual([s.source_id for s in srcs], ["NZ_GETS"])

    def test_unknown_include_id_raises(self):
        with self.assertRaises(ValueError):
            sources_for_query("x", include=("NOT_A_SOURCE",))


class TestHuntMultiMerging(unittest.TestCase):
    def _sources(self, ted_notices=(), gets_items=(), uk_items=()):
        return [
            Source(source_id="TED", fetch_items=lambda: list(ted_notices),
                   normalise=normalise_ted, server_side_filterable=True),
            Source(source_id="NZ_GETS", fetch_items=lambda: list(gets_items),
                   normalise=normalise_gets_nz, server_side_filterable=False,
                   keyword_fields=("title", "description")),
            Source(source_id="UK_CONTRACTS_FINDER", fetch_items=lambda: list(uk_items),
                   normalise=normalise_uk_contracts_finder,
                   server_side_filterable=False,
                   keyword_fields=("title", "description")),
        ]

    def test_merges_entries_across_every_source(self):
        r = hunt_multi(
            "cyber security", SOLO,
            self._sources(ted_notices=[degewo_notice()],
                           gets_items=[gets_item()], uk_items=[uk_item()]))
        self.assertEqual(r.assessed, 3)
        self.assertEqual({e.source for e in r.entries},
                          {"TED", "NZ_GETS", "UK_CONTRACTS_FINDER"})

    def test_fetched_counts_every_raw_item_before_filtering(self):
        r = hunt_multi(
            "cyber security", SOLO,
            self._sources(gets_items=[gets_item(title="totally unrelated topic",
                                                  description="nothing relevant")]))
        self.assertEqual(r.fetched, 1)
        self.assertEqual(r.assessed, 0)

    def test_client_side_keyword_filter_excludes_non_matching_items(self):
        matching = gets_item(key="m", title="Cyber security review")
        non_matching = gets_item(key="n", title="Road resurfacing works",
                                  description="asphalt and gravel")
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[matching, non_matching]))
        self.assertEqual(r.assessed, 1)
        self.assertEqual(r.entries[0].publication_number, "m")

    def test_keyword_filter_is_case_insensitive(self):
        item = gets_item(title="CYBER SECURITY tender")
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[item]))
        self.assertEqual(r.assessed, 1)

    def test_ted_is_never_client_side_filtered(self):
        # TED is server_side_filterable -- hunt_multi() must not apply
        # the client-side keyword filter to it even though the notice's
        # own title text does not literally contain the query string.
        r = hunt_multi("totally different query text", SOLO,
                        self._sources(ted_notices=[degewo_notice()]))
        self.assertEqual(r.assessed, 1)

    def test_ordered_by_band_across_sources(self):
        r = hunt_multi(
            "cyber security", SOLO,
            self._sources(ted_notices=[degewo_notice()],  # DISQUALIFIED
                           gets_items=[gets_item()]))       # INSUFFICIENT_DATA
        bands = [e.band for e in r.entries]
        self.assertLess(bands.index("INSUFFICIENT_DATA"), bands.index("DISQUALIFIED"))

    def test_refuses_empty_source_list(self):
        with self.assertRaises(HuntIntegrityError):
            hunt_multi("q", SOLO, [])

    def test_refuses_empty_query(self):
        with self.assertRaises(HuntIntegrityError):
            hunt_multi("  ", SOLO, self._sources(ted_notices=[degewo_notice()]))

    def test_refuses_wrong_operator_type(self):
        with self.assertRaises(HuntIntegrityError):
            hunt_multi("q", "not a profile", self._sources())

    def test_normaliser_rejection_is_recorded_not_dropped(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[
                            {"title": "cyber security tender, no identity"}]))
        self.assertEqual(r.fetched, 1)
        self.assertEqual(r.assessed, 0)
        self.assertEqual(len(r.skipped), 1)
        self.assertIn("NZ_GETS", r.skipped[0])

    def test_a_failing_source_does_not_blind_the_others(self):
        def boom():
            raise RuntimeError("network exploded")
        sources = [
            Source(source_id="BROKEN", fetch_items=boom, normalise=lambda i: i,
                   server_side_filterable=False, keyword_fields=("title",)),
            Source(source_id="NZ_GETS", fetch_items=lambda: [gets_item()],
                   normalise=normalise_gets_nz, server_side_filterable=False,
                   keyword_fields=("title", "description")),
        ]
        r = hunt_multi("cyber security", SOLO, sources)
        self.assertEqual(r.assessed, 1)
        self.assertTrue(any("BROKEN" in s for s in r.skipped))

    def test_objective_names_every_source(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(ted_notices=[degewo_notice()]))
        self.assertIn("TED", r.objective)
        self.assertIn("NZ_GETS", r.objective)
        self.assertIn("UK_CONTRACTS_FINDER", r.objective)


class TestSignalShapeAcrossSources(unittest.TestCase):
    """Regression coverage for the "signal_fn receives the RAW item,
    never the TED-shaped normalised notice" fix. `hunt_multi()` used to
    hand every source's `signal_fn` the post-`normalise()` dict, which
    is TED-shaped (publication-number, notice-title) for every source
    -- silently hollow for GETS/UK CF (whose signal functions read
    their own raw field names) and, for TED itself, still wrong because
    `ted_signal()` needs `parse_items()`'s flat shape, not the raw
    hyphenated one. A test asserting only "a signal exists" would pass
    while every field on it was empty, so these assert real content."""

    def test_ted_signal_deadline_is_populated_through_hunt_multi(self):
        notice = degewo_notice()
        notice["deadline-receipt-request"] = ["2026-09-22T12:00:00+02:00"]
        src = Source(source_id="TED", fetch_items=lambda: [notice],
                     normalise=normalise_ted, server_side_filterable=True,
                     signal_fn=_ted_signal_from_raw)
        cap = CapabilityProfile(name="pentest", declared_by="operator",
                                 keywords=frozenset({"penetration"}))
        r = hunt_multi("penetration", SOLO, [src], capability=cap)
        self.assertEqual(r.assessed, 1)
        self.assertEqual(r.entries[0].signal.facts["deadline"],
                          "2026-09-22T12:00:00+02:00")

    def test_gets_signal_reads_the_raw_item_not_the_normalised_notice(self):
        # gets_signal() reads "organisation"/"close_date"/"rfx_id" --
        # none of which exist on the TED-shaped normalised dict. If
        # hunt_multi() ever regresses to passing the normalised notice,
        # these fields go silently empty rather than raising.
        from foundation.mouth_gets_nz import gets_signal
        src = Source(source_id="NZ_GETS",
                     fetch_items=lambda: [gets_item(organisation="MFAT")],
                     normalise=normalise_gets_nz, server_side_filterable=False,
                     keyword_fields=("title", "description"),
                     signal_fn=gets_signal)
        cap = CapabilityProfile(name="pentest", declared_by="operator",
                                 keywords=frozenset({"penetration"}))
        r = hunt_multi("cyber security", SOLO, [src], capability=cap)
        self.assertEqual(r.assessed, 1)
        self.assertIn("MFAT", r.entries[0].signal.claim)
        self.assertEqual(r.entries[0].signal.evidence["close_date"], "1 Oct 2026")

    def test_tender_signal_reads_the_raw_item_not_the_normalised_notice(self):
        from foundation.tender_radar import tender_signal
        src = Source(source_id="UK_CONTRACTS_FINDER",
                     fetch_items=lambda: [uk_item(buyer_name="Home Office")],
                     normalise=normalise_uk_contracts_finder,
                     server_side_filterable=False,
                     keyword_fields=("title", "description"),
                     signal_fn=tender_signal)
        cap = CapabilityProfile(name="pentest", declared_by="operator",
                                 keywords=frozenset({"penetration"}))
        r = hunt_multi("cyber security", SOLO, [src], capability=cap)
        self.assertEqual(r.assessed, 1)
        self.assertIn("Home Office", r.entries[0].signal.claim)
        self.assertEqual(r.entries[0].signal.money_observed, "50000 GBP")


class TestHonestyRule(unittest.TestCase):
    """The load-bearing property this whole module exists to guarantee:
    a source that publishes no bidder criteria can only ever produce
    INSUFFICIENT_DATA, never QUALIFIED and never DISQUALIFIED -- even
    when every OTHER field the normaliser knows how to read is
    supplied."""

    def _sources(self, gets_items=(), uk_items=()):
        return [
            Source(source_id="NZ_GETS", fetch_items=lambda: list(gets_items),
                   normalise=normalise_gets_nz, server_side_filterable=False,
                   keyword_fields=("title", "description")),
            Source(source_id="UK_CONTRACTS_FINDER", fetch_items=lambda: list(uk_items),
                   normalise=normalise_uk_contracts_finder,
                   server_side_filterable=False,
                   keyword_fields=("title", "description")),
        ]

    def test_nz_gets_notice_is_always_insufficient_data(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[gets_item()]))
        self.assertEqual(r.assessed, 1)
        self.assertEqual(r.entries[0].band, "INSUFFICIENT_DATA")

    def test_uk_contracts_finder_notice_is_always_insufficient_data(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(uk_items=[uk_item()]))
        self.assertEqual(r.assessed, 1)
        self.assertEqual(r.entries[0].band, "INSUFFICIENT_DATA")

    def test_neither_criteria_less_source_ever_produces_qualified(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[gets_item(key="g")],
                                      uk_items=[uk_item(release_id="u")]))
        bands = {e.band for e in r.entries}
        self.assertNotIn("QUALIFIED", bands)
        self.assertNotIn("DISQUALIFIED", bands)
        self.assertEqual(bands, {"INSUFFICIENT_DATA"})

    def test_no_blocking_clause_is_ever_fabricated(self):
        r = hunt_multi("cyber security", SOLO,
                        self._sources(gets_items=[gets_item()]))
        self.assertEqual(r.entries[0].blocking_clauses, ())


if __name__ == "__main__":
    unittest.main()


class TestRegistryAndFactoryAgree(unittest.TestCase):
    """ALL_SOURCES and sources_for_query() must name the same sources.

    Found 2026-09-02 by an end-to-end run: UK_FIND_A_TENDER and
    ETENDERS_IE were in ALL_SOURCES, fully built, individually loadable
    -- and unreachable from the operator CLI under any keyword, because
    sources_for_query() is what the CLI calls and it named only three.
    A source registered in one list and not the other exists everywhere
    except where someone would actually use it, which is the same class
    of gap as a mouth with no production caller."""

    def test_every_all_sources_id_is_buildable_by_the_factory(self):
        from foundation.sources import ALL_SOURCES, sources_for_query
        for src in ALL_SOURCES:
            built = sources_for_query("x", include=[src.source_id])
            self.assertEqual(len(built), 1)
            self.assertEqual(built[0].source_id, src.source_id)

    def test_default_factory_returns_every_registered_source(self):
        from foundation.sources import ALL_SOURCES, sources_for_query
        self.assertEqual(
            sorted(s.source_id for s in sources_for_query("x")),
            sorted(s.source_id for s in ALL_SOURCES))
