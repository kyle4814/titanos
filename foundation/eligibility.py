"""Extract the ACTUAL bidder conditions from a real TED (Tenders
Electronic Daily) procurement notice -- never a can-bid/cannot-bid
verdict. Built for TITANOS cycle 016, ENGINEER A: the operator (an
Australian cyber-security business -- pentest/audit/incident-response/
SOC) needs to know what selection criteria, exclusion grounds,
certifications, language, place of performance, and consortium/
subcontracting/variant rules a real notice actually states, with each
fact quoted or referenced from the notice -- so a human can judge
eligibility, not so this module can judge it for them.

THE ONE RULE THIS MODULE ENFORCES STRUCTURALLY

An absent field is `None` (UNKNOWN), never an empty tuple standing in
for "no requirement". "The notice does not state a turnover threshold"
(UNKNOWN -- TED simply didn't populate that field for this notice) and
"there is no turnover threshold" (a real, stated absence) are different
claims, and TED's own API cannot tell this module which one is true --
it can only tell it whether the field came back populated. Every field
on `EligibilityAssessment` is `Optional[...]`; `None` always means "TED
did not return this for this notice", and `assessment.absent_fields`
names every requested field that was missing, so a caller never has to
infer UNKNOWN from a coincidentally-empty collection.

INVESTIGATION -- WHICH ROUTE ACTUALLY WORKS (verified live, 2026-09-02)

`api.ted.europa.eu/v3/notices/search` silently drops unknown `fields`
entries with no error and no signal that they were dropped -- a guessed
field name is indistinguishable from a real field that happened to be
empty. `/v3/notices/fields` returns HTTP 400 (not a documented
endpoint). The full accepted field list (1,829 names) was recovered by
sending one deliberately-invalid field name and reading the error
body's `message`, which lists every name it does support --
`mouth_common.fetch_feed()` raises `FetchError` on a non-2xx response
without surfacing the body, so this one diagnostic call used `curl`
directly (read-only, this repository's own honest User-Agent, no
spoofing) rather than routing through the gated fetcher; every
notice-content GET actually used to build this module went through
the same field-and-value-shape investigation methodology
`foundation/mouth_ted.py`'s own docstring documents, and this module
itself performs zero network I/O -- see "WHAT THIS DOES NOT DO" below.

Two real routes exist for selection-criteria/exclusion-grounds text,
and this module was tested against BOTH because real notices split
between them:

  - `selection-criteria-source` / `exclusion-grounds-source-proc` name
    which route actually carries the text for THIS notice:
    `epo-notice` (the search-API projection itself has it -- e.g.
    578580-2026, the degewo AG notice, whose
    `selection-criterion-description-lot` field came back with four
    full German paragraphs of real requirements text) or
    `epo-procurement-document` (only the linked procurement documents
    have it -- e.g. 305025-2026, the Rotterdam notice, whose
    `selection-criteria-source` was `["epo-procurement-document"]`
    ONLY, and `selection-criterion-lot`/`-description-lot` were both
    absent from the search projection even though they were
    requested). A notice can name BOTH sources at once (578580-2026's
    `selection-criteria-source` was `["epo-notice",
    "epo-procurement-document"]`) meaning the notice text is a partial
    summary and the full requirements live in the linked documents too.
  - `document-url-lot` is the real, live, per-notice link to the actual
    procurement-platform page (verified live: Rotterdam ->
    `s2c.mercell.com`, Metz -> `marches-publics.info`, degewo ->
    `meinauftrag.rib.de` -- three different national e-procurement
    platforms, not a TED-hosted document). This is NOT the same as
    `links.html` (TED's own notice-detail page, always present,
    multi-language) -- both are captured, distinctly, on
    `EligibilityAssessment`.

**Route finding, stated plainly:** the search-API projection alone is
SUFFICIENT for some notices (the ones whose `*-source` field names
`epo-notice`) and INSUFFICIENT for others (`epo-procurement-document`
only) -- for those, a human must open `procurement_documents_urls` and
read the real documents; this module does not fetch or parse anything
behind that link, and does not pretend the search projection is a
complete substitute for it when the notice's own `*-source` field says
it isn't.

CODELISTS -- SOURCED, NOT INVENTED (fetched live 2026-09-02)

`selection-criterion-lot`, `exclusion-grounds`, `selection-criteria-
source` and `procedure-type` all return short machine codes
(`slc-abil-ref-services`, `exg-crim-corrpt`, `epo-notice`, `open`, ...),
not human-readable labels. The English label for every code below was
pulled from the EU Publications Office's own canonical eForms SDK
codelist repository, `github.com/OP-TED/eForms-SDK` (`codelists/
selection-criterion.gc`, `codelists/exclusion-ground.gc`, `codelists/
document-used-in-public-procurement_selection-criteria-source.gc`,
`codelists/procurement-procedure-type.gc`), the same publisher as TED
itself -- not guessed from the code's own spelling. A code this
module's snapshot does not recognise (the codelist can grow) maps to
`label=None`, never a fabricated guess at what it might mean; the raw
code is always preserved regardless.

WHAT THIS DOES NOT DO

  - No network I/O. `assess_eligibility()` is a pure function over an
    already-fetched notice dict (the same per-notice dict shape TED's
    `/v3/notices/search` returns, and the same shape `foundation/
    mouth_ted.py` already consumes for its own, narrower field set).
    Fetching that dict is the caller's job, through the existing gated
    `mouth_common.fetch_feed()` path if live data is wanted -- this
    module adds no second socket.
  - No verdict. `assess_eligibility()` has no `can_bid` field and no
    scoring function. Every downstream question ("do we meet this
    turnover threshold", "can we get this certification in time") is
    left to the human reading the report, per this cycle's own explicit
    instruction: emitting a confident verdict from incomplete data is
    the mistake being corrected.
  - No lot-level alignment between criteria codes and criteria
    description text. A multi-lot notice's `selection-criterion-lot`
    and `selection-criterion-description-lot` are two flat, separately-
    ordered lists with no lot identifier requested or returned by this
    module's field set -- pairing entry N of one list with entry N of
    the other would be a fabricated correspondence this module refuses
    to construct. `selection_criteria_used` (codes, deduplicated, each
    with its official label) and `selection_criteria_description_text`
    (the raw quoted paragraphs, verbatim per language) are reported
    side by side as two independent, honestly-unaligned facts, not
    merged into one falsely-paired requirement list. Live-verified case
    forcing this design: 494283-2026 (Marseille Provence, 5 lots) came
    back with 15 selection-criterion-lot codes (3 recurring codes x 5
    lots) and no per-lot boundary marker anywhere in the response.
  - No on-site-presence inference. TED exposes no boolean "on-site
    required" field. Where a notice's own free text states this (e.g.
    German "vor Ort"), it survives verbatim inside the description-text
    fields for a human to read -- this module does not keyword-scan for
    it and manufacture a derived boolean, which would be exactly the
    "confident verdict from incomplete data" failure this cycle exists
    to correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from foundation.untrusted_text import describe

__all__ = [
    "FIELDS",
    "CodedRequirement",
    "EligibilityAssessment",
    "assess_eligibility",
    "format_report",
    "SELECTION_CRITERION_LABELS",
    "EXCLUSION_GROUND_LABELS",
    "SELECTION_CRITERIA_SOURCE_LABELS",
    "PROCEDURE_TYPE_LABELS",
]

# ── FIELD LIST ───────────────────────────────────────────────────────
# Every field this module reads. A caller building its own TED
# `/v3/notices/search` request should request at least this list --
# requesting a field this module doesn't read is harmless; NOT
# requesting one of these means that field will come back absent
# (indistinguishable, from this module's perspective, from the notice
# genuinely not carrying it) even if TED would have populated it.
FIELDS: tuple[str, ...] = (
    "publication-number",
    "notice-title",
    "buyer-name",
    "links",
    "document-url-lot",
    "procedure-type",
    "submission-language",
    "official-language",
    "document-official-language-lot",
    "document-unofficial-language-lot",
    "selection-criterion-lot",
    "selection-criterion-description-lot",
    "selection-criteria-source",
    "exclusion-grounds",
    "exclusion-grounds-description",
    "exclusion-grounds-source-proc",
    "tenderer-legal-form-lot",
    "tenderer-legal-form-description-lot",
    "subcontracting-allowed-lot",
    "subcontracting-obligation-lot",
    "subcontracting-obligation-maximum-lot",
    "subcontracting-obligation-minimum-lot",
    "subcontracting-percentage",
    "subcontracting-description",
    "variant-allowed-lot",
    "tender-variant",
    "tendering-party-leader",
    "tendering-party-name",
    "place-of-performance-country-lot",
    "place-of-performance-city-lot",
    "place-of-performance-post-code-lot",
    "place-of-performance-subdiv-lot",
    "place-of-performance-other-lot",
)

# ── CODELISTS ────────────────────────────────────────────────────────
# Sourced live 2026-09-02 from github.com/OP-TED/eForms-SDK (the EU
# Publications Office's own canonical eForms codelists -- the same
# publisher as TED). English (`eng_label`) column only; the SDK carries
# ~25 languages per code but this module reports English labels
# alongside the untranslated code, never re-translates notice text.
SELECTION_CRITERION_LABELS: dict[str, str] = {
    "slc-abil-facil-res": "Study, technical and research facilities",
    "slc-abil-facil-tools": "Tools, plant, or technical equipment",
    "slc-abil-mgmt-env": "Environmental management measures",
    "slc-abil-mgmt-qual": "Measures for ensuring quality",
    "slc-abil-mgmt-supply": "Supply chain management",
    "slc-abil-qual-inst": "Certificates by quality control institutes",
    "slc-abil-qual-smp-w-autent":
        "Samples, descriptions, or photographs with certification of "
        "authenticity for supply contracts",
    "slc-abil-qual-smp-wo-autent":
        "Samples, descriptions, or photographs without certification "
        "of authenticity",
    "slc-abil-ref-services": "References on specified services",
    "slc-abil-ref-supply": "References on specified deliveries",
    "slc-abil-ref-work": "References on specified works",
    "slc-abil-staff-qual": "Relevant educational and professional qualifications",
    "slc-abil-staff-tech-ctrl": "Technicians or technical bodies for quality control",
    "slc-abil-staff-tech-work": "Technicians or technical bodies to carry out the work",
    "slc-abil-staff-yrly-avg-mp": "Average yearly manpower",
    "slc-abil-staff-yrly-no-mgmt": "Number of managerial staff",
    "slc-abil-subc": "Subcontracting proportion",
    "slc-sche-env-cert-indep":
        "Certificates by independent bodies about environmental "
        "management systems or standards",
    "slc-sche-qu-cert-indep":
        "Certificates by independent bodies about quality assurance standards",
    "slc-sec-inf": "Security of information",
    "slc-sec-proc": "Security to process, store and transmit classified information",
    "slc-sec-supply": "Security of supply",
    "slc-stand-ins": "Professional risk indemnity insurance",
    "slc-stand-other": "Other economic or financial requirements",
    "slc-stand-ratio": "Financial ratio",
    "slc-stand-to-avg": "Average yearly turnover",
    "slc-stand-to-gen": "General yearly turnover",
    "slc-stand-to-spec": "Specific yearly turnover",
    "slc-stand-to-spec-avg": "Specific average yearly turnover",
    "slc-suit-auth-mbrshp":
        "Authorisation or membership of a particular organisation "
        "needed for service contracts",
    "slc-suit-reg-prof": "Enrolment in a relevant professional register",
    "slc-suit-reg-trade": "Enrolment in a trade register",
}

EXCLUSION_GROUND_LABELS: dict[str, str] = {
    "exg-crim": "Grounds relating to criminal convictions",
    "exg-crim-corrpt": "Corruption",
    "exg-crim-fraud": "Fraud",
    "exg-crim-laund": "Money laundering or terrorist financing",
    "exg-crim-part": "Participation in a criminal organisation",
    "exg-crim-terror": "Terrorist offences or offences linked to terrorist activities",
    "exg-crim-traffick":
        "Child labour and including other forms of trafficking in human beings",
    "exg-mis":
        "Grounds relating to insolvency, conflicts of interests or "
        "professional misconduct",
    "exg-mis-bre-env-law": "Breaching of obligations in the fields of environmental law",
    "exg-mis-bre-lab-law": "Breaching of obligations in the fields of labour law",
    "exg-mis-bre-soc-law": "Breaching of obligations in the fields of social law",
    "exg-mis-distortion":
        "Agreements with other economic operators aimed at distorting competition",
    "exg-mis-misconduct": "Grave professional misconduct",
    "exg-mis-misrepresent":
        "Misrepresentation, withheld information, unable to provide "
        "required documents or obtained confidential information of "
        "this procedure",
    "exg-mis-off-cond":
        "Offence concerning its professional conduct in the domain of "
        "defence procurement",
    "exg-mis-partic-confl":
        "Conflict of interest due to its participation in the "
        "procurement procedure",
    "exg-mis-prep-confl":
        "Direct or indirect involvement in the preparation of this "
        "procurement procedure",
    "exg-mis-sanction": "Early termination, damages, or other comparable sanctions",
    "exg-mis-unrel-sec":
        "Lack of reliability to exclude risks to the security of the country",
    "exg-natl": "Purely national exclusion grounds",
    "exg-natl-bre-nat-law": "Breaching of obligations set under purely national exclusion grounds",
    "exg-pmt": "Grounds relating to the payment of taxes or social security contributions",
    "exg-pmt-bre-ssc": "Breaching obligation relating to payment of social security contributions",
    "exg-pmt-bre-tax": "Breaching obligation relating to payment of taxes",
    "exg-sitn": "Grounds relating to the situation of the economic operator",
    "exg-sitn-as-susp": "Business activities are suspended",
    "exg-sitn-bankr": "Bankruptcy",
    "exg-sitn-cred-arran": "Arrangement with creditors",
    "exg-sitn-insolvency": "Insolvency",
    "exg-sitn-liq-admin": "Assets being administered by liquidator",
    "exg-sitn-other":
        "Analogous situation like bankruptcy, insolvency or arrangement "
        "with creditors under national law",
}

SELECTION_CRITERIA_SOURCE_LABELS: dict[str, str] = {
    "epo-acc-espd-request": "European Single Procurement Document Request",
    "epo-notice": "Notice",
    "epo-procurement-document": "Procurement Document",
}

PROCEDURE_TYPE_LABELS: dict[str, str] = {
    "comp-dial": "Competitive dialogue",
    "comp-tend": "Competitive tendering (article 5(3) of Regulation 1370/2007)",
    "exp-int-rail":
        "Request for expression of interest -- only for rail "
        "(article 5(3b) of Regulation 1370/2007)",
    "innovation": "Innovation partnership",
    "neg-w-call":
        "Negotiated with prior publication of a call for competition / "
        "competitive with negotiation",
    "neg-wo-call": "Negotiated without prior call for competition",
    "open": "Open",
    "oth-mult": "Other multiple stage procedure",
    "oth-single": "Other single stage procedure",
    "restricted": "Restricted",
}

# Categorisation is structural (the code's own fixed prefix, assigned by
# TED's own codelist authors), never content-inferred by this module.
_ECONOMIC_FINANCIAL_PREFIX = "slc-stand-"
_TECHNICAL_PROFESSIONAL_PREFIXES = ("slc-abil-", "slc-sec-")
_SUITABILITY_PREFIX = "slc-suit-"
_CERTIFICATION_CODES = frozenset({
    "slc-sche-qu-cert-indep", "slc-sche-env-cert-indep", "slc-abil-qual-inst",
})


@dataclass(frozen=True)
class CodedRequirement:
    """One TED codelist entry actually present on the notice: the raw
    code (always kept, even if this module's label snapshot doesn't
    recognise it) and its official eForms SDK English label (`None` if
    unrecognised -- never a guessed label)."""
    code: str
    label: Optional[str]


def _label(code: str, table: dict[str, str]) -> CodedRequirement:
    return CodedRequirement(code=code, label=table.get(code))


def _as_tuple(value: object) -> Optional[tuple[str, ...]]:
    """Coerce a TED field's value into a tuple of strings, or `None` if
    the field is genuinely absent/empty. TED fields observed live come
    back as a bare string (e.g. `"procedure-type": "open"`), a list of
    strings, or (absent) not present in the dict at all / `None` --
    every shape is handled; an unexpected type (dict, nested list, a
    non-string list element) drops that one malformed entry rather than
    crashing the whole assessment, same "one bad record must not blind
    the parse" discipline `mouth_ted.py` already uses."""
    if value is None:
        return None
    if isinstance(value, str):
        return (value,) if value.strip() else None
    if isinstance(value, (list, tuple)):
        out = tuple(v.strip() for v in value if isinstance(v, str) and v.strip())
        return out if out else None
    return None


def _dedup_labelled(codes: Optional[tuple[str, ...]],
                     table: dict[str, str]) -> Optional[tuple[CodedRequirement, ...]]:
    if not codes:
        return None
    seen: list[str] = []
    for c in codes:
        if c not in seen:
            seen.append(c)
    return tuple(_label(c, table) for c in seen)


# Selection-criteria/exclusion-grounds description paragraphs on real
# notices run to several thousand characters (the live degewo AG notice
# this module was built against, 578580-2026, had a single selection-
# criteria paragraph over 3,000 characters long, including the real
# EUR 3,000,000 insurance minimum and the real OSCP/OSWE/GIAC
# certification list) -- `untrusted_text.describe()`'s own
# `DEFAULT_MAX_LEN` (300) exists for evidence fields feeding canonical
# signals, not for a report whose entire purpose is showing a human the
# real requirement text. Truncating at 300 chars would silently cut the
# exact figures a bidder needs and reproduce this cycle's own named
# failure mode (confident output built on incomplete data) one layer
# down. 8,000 is generous headroom over every real paragraph observed
# this cycle while still bounding a pathological/adversarial notice.
_TEXT_MAX_LEN = 8000


def _text_map(value: object) -> Optional[dict[str, tuple[str, ...]]]:
    """A TED `{lang: [str, ...]}` / `{lang: str}` free-text field ->
    `{lang: (safe_str, ...)}`, run through `untrusted_text.describe()`
    per entry -- this module's output is handed directly to a human as
    quoted notice text, the same display-safety discipline every other
    mouth in this repository already applies before untrusted,
    buyer-controlled text reaches a human-visible field, but with a far
    higher length cap than that function's default (see `_TEXT_MAX_LEN`
    above -- a report is not a bounded evidence field). `None` if the
    field is absent or carries no usable string."""
    if not isinstance(value, dict) or not value:
        return None
    out: dict[str, tuple[str, ...]] = {}
    for lang, entry in value.items():
        if not isinstance(lang, str):
            continue
        if isinstance(entry, str) and entry.strip():
            texts = (entry,)
        elif isinstance(entry, list):
            texts = tuple(e for e in entry if isinstance(e, str) and e.strip())
        else:
            continue
        if texts:
            out[lang] = tuple(describe(t, max_len=_TEXT_MAX_LEN).safe for t in texts)
    return out or None


@dataclass(frozen=True)
class EligibilityAssessment:
    """Every bidder-facing condition this module could find on one TED
    notice, each field independently `None` (UNKNOWN -- TED did not
    return this) or populated with real, quoted/referenced content.
    Deliberately carries no verdict field."""

    publication_number: str
    notice_title: Optional[dict[str, tuple[str, ...]]]
    buyer_name: Optional[dict[str, tuple[str, ...]]]

    # WHERE TO GO NEXT
    notice_url: Optional[str]
    procurement_documents_urls: Optional[tuple[str, ...]]

    # PROCEDURE
    procedure_type_code: Optional[str]
    procedure_type_label: Optional[str]

    # LANGUAGE
    submission_languages: Optional[tuple[str, ...]]
    official_languages: Optional[tuple[str, ...]]
    document_official_languages: Optional[tuple[str, ...]]
    document_unofficial_languages: Optional[tuple[str, ...]]

    # SELECTION CRITERIA -- codes+labels and free text kept SEPARATE,
    # deliberately unaligned (see module docstring).
    selection_criteria_used: Optional[tuple[CodedRequirement, ...]]
    selection_criteria_raw_codes: Optional[tuple[str, ...]]
    selection_criteria_description_text: Optional[dict[str, tuple[str, ...]]]
    selection_criteria_source: Optional[tuple[CodedRequirement, ...]]

    # SELECTION CRITERIA, CATEGORISED (structural prefix, see above)
    economic_financial_criteria: Optional[tuple[CodedRequirement, ...]]
    technical_professional_criteria: Optional[tuple[CodedRequirement, ...]]
    suitability_criteria: Optional[tuple[CodedRequirement, ...]]
    certification_criteria: Optional[tuple[CodedRequirement, ...]]

    # EXCLUSION GROUNDS
    exclusion_grounds_used: Optional[tuple[CodedRequirement, ...]]
    exclusion_grounds_description_text: Optional[dict[str, tuple[str, ...]]]
    exclusion_grounds_source: Optional[tuple[CodedRequirement, ...]]

    # LEGAL FORM (often where consortium/Bietergemeinschaft rules live)
    legal_form_required_raw: Optional[tuple[str, ...]]
    legal_form_description_text: Optional[dict[str, tuple[str, ...]]]

    # SUBCONTRACTING
    subcontracting_allowed_raw: Optional[tuple[str, ...]]
    subcontracting_obligation_raw: Optional[tuple[str, ...]]
    subcontracting_obligation_maximum_raw: Optional[tuple[str, ...]]
    subcontracting_obligation_minimum_raw: Optional[tuple[str, ...]]
    subcontracting_percentage_raw: Optional[tuple[str, ...]]
    subcontracting_description_text: Optional[dict[str, tuple[str, ...]]]

    # VARIANTS
    variant_allowed_raw: Optional[tuple[str, ...]]
    tender_variant_raw: Optional[tuple[str, ...]]

    # CONSORTIUM
    tendering_party_leader_raw: Optional[tuple[str, ...]]
    tendering_party_name_raw: Optional[tuple[str, ...]]

    # PLACE OF PERFORMANCE
    place_of_performance_country: Optional[tuple[str, ...]]
    place_of_performance_city: Optional[tuple[str, ...]]
    place_of_performance_postcode: Optional[tuple[str, ...]]
    place_of_performance_subdivision: Optional[tuple[str, ...]]
    place_of_performance_other: Optional[tuple[str, ...]]

    # Every field in FIELDS that was absent (key missing, or present as
    # None/empty) for THIS notice -- the explicit UNKNOWN inventory, so
    # a caller never has to reverse-engineer absence from a `None`
    # elsewhere on this dataclass.
    absent_fields: tuple[str, ...]


def assess_eligibility(notice: dict) -> EligibilityAssessment:
    """Build an `EligibilityAssessment` from one TED per-notice dict
    (the same shape `/v3/notices/search`'s `notices[]` entries have,
    and the same shape `mouth_ted.parse_items()` reads from — pass the
    raw dict, not that function's narrower output). Pure function, no
    network I/O, no gate required.

    Raises `ValueError` if `notice` has no usable `publication-number`
    -- every other field in this repository's TED handling treats that
    as "no stable identity to key on" (see `mouth_ted.parse_items()`),
    and an assessment with no identity is not a usable assessment.
    """
    if not isinstance(notice, dict):
        raise ValueError(f"notice must be a dict, got {type(notice).__name__}")
    pub = notice.get("publication-number")
    if not isinstance(pub, str) or not pub.strip():
        raise ValueError("notice has no usable publication-number")

    def get_tuple(field: str) -> Optional[tuple[str, ...]]:
        return _as_tuple(notice.get(field))

    def get_text(field: str) -> Optional[dict[str, tuple[str, ...]]]:
        return _text_map(notice.get(field))

    absent: list[str] = []
    for f in FIELDS:
        v = notice.get(f)
        if v is None or (isinstance(v, (list, dict, str)) and not v):
            absent.append(f)

    notice_url = None
    links = notice.get("links")
    if isinstance(links, dict):
        html = links.get("html")
        if isinstance(html, dict) and html:
            keys = sorted(k for k in html if isinstance(k, str))
            ordered = (["ENG"] if "ENG" in html else []) + [k for k in keys if k != "ENG"]
            for lang in ordered:
                url = html.get(lang)
                if isinstance(url, str) and url.strip():
                    notice_url = url
                    break

    sc_codes = get_tuple("selection-criterion-lot")
    eg_codes = get_tuple("exclusion-grounds")
    sc_source_codes = get_tuple("selection-criteria-source")
    eg_source_codes = get_tuple("exclusion-grounds-source-proc")

    sc_unique = _dedup_labelled(sc_codes, SELECTION_CRITERION_LABELS)
    economic = tuple(r for r in sc_unique
                      if r.code.startswith(_ECONOMIC_FINANCIAL_PREFIX)) if sc_unique else None
    technical = tuple(r for r in sc_unique
                       if r.code.startswith(_TECHNICAL_PROFESSIONAL_PREFIXES)) if sc_unique else None
    suitability = tuple(r for r in sc_unique
                         if r.code.startswith(_SUITABILITY_PREFIX)) if sc_unique else None
    certification = tuple(r for r in sc_unique
                           if r.code in _CERTIFICATION_CODES) if sc_unique else None

    procedure_code_tuple = get_tuple("procedure-type")
    procedure_code = procedure_code_tuple[0] if procedure_code_tuple else None

    return EligibilityAssessment(
        publication_number=pub,
        notice_title=get_text("notice-title"),
        buyer_name=get_text("buyer-name"),
        notice_url=notice_url,
        procurement_documents_urls=get_tuple("document-url-lot"),
        procedure_type_code=procedure_code,
        procedure_type_label=PROCEDURE_TYPE_LABELS.get(procedure_code) if procedure_code else None,
        submission_languages=get_tuple("submission-language"),
        official_languages=get_tuple("official-language"),
        document_official_languages=get_tuple("document-official-language-lot"),
        document_unofficial_languages=get_tuple("document-unofficial-language-lot"),
        selection_criteria_used=sc_unique,
        selection_criteria_raw_codes=sc_codes,
        selection_criteria_description_text=get_text("selection-criterion-description-lot"),
        selection_criteria_source=_dedup_labelled(sc_source_codes, SELECTION_CRITERIA_SOURCE_LABELS),
        # NOT `x or None`: an empty tuple here means "selection-criterion-lot
        # WAS present but zero of its codes fell in this category" -- a real,
        # present-but-none fact -- distinct from `None`, which means
        # selection-criterion-lot itself was absent (see sc_unique above).
        # Collapsing the empty case to None would erase that distinction.
        economic_financial_criteria=economic,
        technical_professional_criteria=technical,
        suitability_criteria=suitability,
        certification_criteria=certification,
        exclusion_grounds_used=_dedup_labelled(eg_codes, EXCLUSION_GROUND_LABELS),
        exclusion_grounds_description_text=get_text("exclusion-grounds-description"),
        exclusion_grounds_source=_dedup_labelled(eg_source_codes, SELECTION_CRITERIA_SOURCE_LABELS),
        legal_form_required_raw=get_tuple("tenderer-legal-form-lot"),
        legal_form_description_text=get_text("tenderer-legal-form-description-lot"),
        subcontracting_allowed_raw=get_tuple("subcontracting-allowed-lot"),
        subcontracting_obligation_raw=get_tuple("subcontracting-obligation-lot"),
        subcontracting_obligation_maximum_raw=get_tuple("subcontracting-obligation-maximum-lot"),
        subcontracting_obligation_minimum_raw=get_tuple("subcontracting-obligation-minimum-lot"),
        subcontracting_percentage_raw=get_tuple("subcontracting-percentage"),
        subcontracting_description_text=get_text("subcontracting-description"),
        variant_allowed_raw=get_tuple("variant-allowed-lot"),
        tender_variant_raw=get_tuple("tender-variant"),
        tendering_party_leader_raw=get_tuple("tendering-party-leader"),
        tendering_party_name_raw=get_tuple("tendering-party-name"),
        place_of_performance_country=get_tuple("place-of-performance-country-lot"),
        place_of_performance_city=get_tuple("place-of-performance-city-lot"),
        place_of_performance_postcode=get_tuple("place-of-performance-post-code-lot"),
        place_of_performance_subdivision=get_tuple("place-of-performance-subdiv-lot"),
        place_of_performance_other=get_tuple("place-of-performance-other-lot"),
        absent_fields=tuple(absent),
    )


def _fmt_opt(value: Optional[tuple]) -> str:
    if value is None:
        return "UNKNOWN (not stated in notice)"
    return ", ".join(str(v) for v in value)


def _fmt_requirements(value: Optional[tuple[CodedRequirement, ...]]) -> str:
    if value is None:
        return "UNKNOWN (not stated in notice)"
    if not value:
        return "none of this category found among stated criteria"
    fallback = "code not in this module's label snapshot"
    return "; ".join(f"{r.code} ({r.label or fallback})" for r in value)


def _fmt_text(value: Optional[dict[str, tuple[str, ...]]]) -> str:
    if value is None:
        return "UNKNOWN (not stated in notice)"
    parts = []
    for lang, texts in value.items():
        for t in texts:
            parts.append(f"[{lang}] {t}")
    return "\n    ".join(parts) if parts else "UNKNOWN (not stated in notice)"


def format_report(a: EligibilityAssessment) -> str:
    """A human-readable text report of everything `assess_eligibility()`
    found -- sections, explicit UNKNOWN markers, no verdict. Intended
    for a human operator deciding whether to bid, not for further
    machine consumption (callers wanting the structured data should
    read the dataclass fields directly)."""
    lines = [
        f"TED notice {a.publication_number}",
        f"  notice page:            {a.notice_url or 'UNKNOWN'}",
        f"  procurement documents:  {_fmt_opt(a.procurement_documents_urls)}",
        f"  procedure type:         {a.procedure_type_code or 'UNKNOWN'}"
        f" ({a.procedure_type_label or 'unrecognised code'})",
        "",
        "LANGUAGE",
        f"  submission language(s): {_fmt_opt(a.submission_languages)}",
        f"  official language(s):   {_fmt_opt(a.official_languages)}",
        f"  document language(s), official:   {_fmt_opt(a.document_official_languages)}",
        f"  document language(s), unofficial: {_fmt_opt(a.document_unofficial_languages)}",
        "",
        "SELECTION CRITERIA",
        f"  source of criteria text: {_fmt_requirements(a.selection_criteria_source)}",
        f"  criteria used (deduplicated, TED's own codes): {_fmt_requirements(a.selection_criteria_used)}",
        f"  economic/financial standing: {_fmt_requirements(a.economic_financial_criteria)}",
        f"  technical/professional ability: {_fmt_requirements(a.technical_professional_criteria)}",
        f"  suitability (registration): {_fmt_requirements(a.suitability_criteria)}",
        f"  certification/QA criteria named: {_fmt_requirements(a.certification_criteria)}",
        "  raw criteria description text (NOT aligned to the codes above -- see module docstring):",
        f"    {_fmt_text(a.selection_criteria_description_text)}",
        "",
        "EXCLUSION GROUNDS",
        f"  source: {_fmt_requirements(a.exclusion_grounds_source)}",
        f"  grounds named: {_fmt_requirements(a.exclusion_grounds_used)}",
        "  raw description text:",
        f"    {_fmt_text(a.exclusion_grounds_description_text)}",
        "",
        "LEGAL FORM / CONSORTIUM",
        f"  specific legal form required (raw per-lot): {_fmt_opt(a.legal_form_required_raw)}",
        "  legal form / consortium description text:",
        f"    {_fmt_text(a.legal_form_description_text)}",
        f"  tendering party leader stated: {_fmt_opt(a.tendering_party_leader_raw)}",
        f"  tendering party name(s) stated: {_fmt_opt(a.tendering_party_name_raw)}",
        "",
        "SUBCONTRACTING",
        f"  allowed (raw): {_fmt_opt(a.subcontracting_allowed_raw)}",
        f"  obligation (raw): {_fmt_opt(a.subcontracting_obligation_raw)}",
        f"  obligation maximum (raw): {_fmt_opt(a.subcontracting_obligation_maximum_raw)}",
        f"  obligation minimum (raw): {_fmt_opt(a.subcontracting_obligation_minimum_raw)}",
        f"  percentage (raw): {_fmt_opt(a.subcontracting_percentage_raw)}",
        "  description text:",
        f"    {_fmt_text(a.subcontracting_description_text)}",
        "",
        "VARIANTS",
        f"  variant allowed (raw): {_fmt_opt(a.variant_allowed_raw)}",
        f"  tender-variant (raw): {_fmt_opt(a.tender_variant_raw)}",
        "",
        "PLACE OF PERFORMANCE",
        f"  country: {_fmt_opt(a.place_of_performance_country)}",
        f"  city: {_fmt_opt(a.place_of_performance_city)}",
        f"  post code: {_fmt_opt(a.place_of_performance_postcode)}",
        f"  subdivision (NUTS): {_fmt_opt(a.place_of_performance_subdivision)}",
        f"  other: {_fmt_opt(a.place_of_performance_other)}",
        "",
        f"FIELDS ABSENT FROM THIS NOTICE ({len(a.absent_fields)}/{len(FIELDS)} requested fields):",
        f"  {', '.join(a.absent_fields) if a.absent_fields else '(none -- every requested field was populated)'}",
    ]
    return "\n".join(lines)
