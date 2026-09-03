"""Build the reusable supplier-registration answer set once, instead of
re-typing the same capability statement / category mapping / standard
declaration answers into NSW's Supplier Hub, the UK CCS Selection
Questionnaire, ICN Gateway, and the QLD Supplier Portal, four separate
times. See `AU_PANEL_CHECKLIST.md` and `LIVE_TARGET_REQUIREMENTS.md`
for the four live targets this module was built against.

THE ABSOLUTE RULE THIS MODULE ENFORCES STRUCTURALLY

This module NEVER generates, invents, infers, guesses, or placeholders
any of: ABN, ACN, licence number, registration number, insurance policy
number or cover amount, certification, customer name, revenue figure,
referee, past contract, or years of experience. If a fact is not
explicitly supplied by the operator, the rendered output carries the
literal string `UNKNOWN_MARKER` ("UNKNOWN -- VERIFICATION REQUIRED") in
its place -- never a plausible-looking synthesised value. Supplier
registrations carry legal declarations to a government body; a
fabricated field here would be a false declaration this module has no
authority to make on the operator's behalf.

This is enforced by construction, not by convention: `_fact()` is the
ONLY function in this module permitted to read an optional field and
decide what text represents it, and it returns `UNKNOWN_MARKER` for
every falsy/absent value with no branch that synthesises a substitute.
Every rendering function in this module reads facts exclusively through
`_fact()`/`_facts_list()` -- there is no code path that writes a digit
string, a name, or a figure into the output except by copying a value
the caller actually supplied on `OperatorProfile` or `BusinessFacts`.

WHAT THIS MODULE REUSES, NOT DUPLICATES

`OperatorProfile` (name, staff_count, certifications, insurance_cover_eur,
corporate_references, languages) is imported from
`foundation/qualification.py`, not redefined here -- this module treats
it as read-only and adds no fields to it. Everything NSW/UK/ICN/QLD ask
for that `OperatorProfile` does not carry (ABN, ACN, licence/registration
numbers, AUD-denominated insurance figures, referee contact details,
declared service-capability keywords, years of experience, revenue band)
lives in this module's own `BusinessFacts` -- a second, additive
declaration, not a competing profile type.

WHAT THIS DOES NOT DO

  - No network I/O.
  - Never renders a completed-looking, submission-ready application.
    Every section is stamped `DRAFT_STAMP` and the module-level
    docstring plus `render_dossier()`'s own trailing note make explicit
    that this is preparation material a human transcribes, checks, and
    signs -- never something submitted directly.
  - Never auto-affirms a legal declaration (financial solvency, supplier
    declaration, terms-and-conditions acceptance) -- those always render
    as an explicit unchecked action for the human, never as a completed
    statement.
  - Does not modify `foundation/qualification.py` or any `.md` file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from foundation.qualification import OperatorProfile

__all__ = [
    "DRAFT_STAMP",
    "UNKNOWN_MARKER",
    "Referee",
    "BusinessFacts",
    "SupplierDossier",
    "MissingFact",
    "missing_facts_for_scheme",
    "render_dossier",
]


# The literal string every unsupplied fact renders as. Never mutated
# with an interpolated placeholder value -- it is either this exact
# string or a value the operator genuinely supplied.
UNKNOWN_MARKER = "UNKNOWN — VERIFICATION REQUIRED"

DRAFT_STAMP = "**DRAFT — REQUIRES HUMAN REVIEW AND SIGNATURE**"

# The four live targets this module was built against
# (`AU_PANEL_CHECKLIST.md`, `LIVE_TARGET_REQUIREMENTS.md`).
SCHEMES = (
    "NSW_ICT_SERVICES_SCHEME",
    "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS",
    "ICN_GATEWAY",
    "QLD_SUPPLIER_PORTAL",
    # The two Irish qualification systems that SURVIVED the campaign's
    # criteria analysis as genuinely pursuable (see OPS_BOARD.md). Added
    # 2026-09-05: the dossier covered four AU/UK schemes but not the two
    # leads with the lowest cost-to-start. Every requirement below is
    # quoted from the real PQQ/QSQ read via eTenders' anonymous download.
    "IARNROD_EIREANN_7289_PENTEST",
    "GAS_NETWORKS_IRELAND_23_049_CYBER",
)

# Category K (Security management) labels, quoted verbatim from
# `AU_PANEL_CHECKLIST.md` Part 1.5 -- this module maps an operator's own
# declared skill keywords onto these labels; it never invents a category
# the operator did not themselves claim a matching skill for.
_NSW_CATEGORY_K = (
    ("K01", "Security strategy including delivery \"as a service\"",
     ("security strategy", "security audit", "vulnerability assessment",
      "iso 27001")),
    ("K02", "Security management security and firewall installation "
            "including delivery \"as a service\"",
     ("firewall installation",)),
    ("K03", "Security testing including delivery \"as a service\"",
     ("penetration testing", "security testing", "web security testing",
      "secure code review", "secure code reviews")),
    ("K04", "Security and firewall management including delivery "
            "\"as a service\"",
     ("firewall management",)),
)


@dataclass(frozen=True)
class Referee:
    """A referee the operator has themselves named -- never generated.
    All three fields are required non-blank strings if a `Referee` is
    constructed at all; an operator with no referees simply supplies an
    empty `referees` tuple on `BusinessFacts` rather than a placeholder
    `Referee`."""

    name: str
    organisation: str
    contact: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("name", self.name), ("organisation", self.organisation),
            ("contact", self.contact),
        ):
            if not value.strip():
                raise ValueError(
                    f"Referee.{field_name} cannot be blank -- an empty "
                    f"referee is not a real referee; omit it from "
                    f"BusinessFacts.referees instead")


@dataclass(frozen=True)
class BusinessFacts:
    """Everything the four live targets ask for that `OperatorProfile`
    does not carry. Every field is optional and defaults to an absent
    state (`None` / empty tuple) -- absence here is honest, not an
    error, and `render_dossier()` renders `UNKNOWN_MARKER` for each
    absent field rather than guessing.

    `skills` is the one field this module reads to derive an honest
    service-category mapping (see `_map_categories()`) -- it must be
    the operator's own plain-language description of what they do
    (e.g. "penetration testing"), not a code the operator is unsure
    they qualify for.
    """

    abn: Optional[str] = None
    acn: Optional[str] = None
    business_address: Optional[str] = None
    licence_number: Optional[str] = None
    registration_number: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_pi_cover_aud: Optional[float] = None
    insurance_pl_cover_aud: Optional[float] = None
    years_experience: Optional[int] = None
    revenue_band: Optional[str] = None
    skills: Tuple[str, ...] = ()
    referees: Tuple[Referee, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.skills, tuple):
            raise ValueError("BusinessFacts.skills must be a tuple")
        if not isinstance(self.referees, tuple):
            raise ValueError("BusinessFacts.referees must be a tuple")
        for r in self.referees:
            if not isinstance(r, Referee):
                raise ValueError(
                    "BusinessFacts.referees must contain only Referee "
                    "instances -- a bare string or dict is not accepted, "
                    "because that would make it too easy to smuggle an "
                    "unstructured, unverified guess in as a referee")
        if self.years_experience is not None and self.years_experience < 0:
            raise ValueError("years_experience cannot be negative")
        if self.insurance_pi_cover_aud is not None and self.insurance_pi_cover_aud < 0:
            raise ValueError("insurance_pi_cover_aud cannot be negative")
        if self.insurance_pl_cover_aud is not None and self.insurance_pl_cover_aud < 0:
            raise ValueError("insurance_pl_cover_aud cannot be negative")
        object.__setattr__(
            self, "skills",
            tuple(s.strip() for s in self.skills if s.strip()))


@dataclass(frozen=True)
class SupplierDossier:
    """The operator's whole declared position: their `OperatorProfile`
    (imported, not redefined) plus their `BusinessFacts`. Pure data --
    `render_dossier()` is the only function that turns this into text.
    """

    profile: OperatorProfile
    facts: BusinessFacts = BusinessFacts()

    def __post_init__(self) -> None:
        if not isinstance(self.profile, OperatorProfile):
            raise ValueError(
                f"SupplierDossier.profile must be an OperatorProfile, "
                f"got {type(self.profile).__name__}")
        if not isinstance(self.facts, BusinessFacts):
            raise ValueError(
                f"SupplierDossier.facts must be a BusinessFacts, "
                f"got {type(self.facts).__name__}")


@dataclass(frozen=True)
class MissingFact:
    """One fact a named scheme requires that this dossier does not yet
    carry -- the finite checklist `missing_facts_for_scheme()` returns.
    """

    scheme: str
    fact: str
    why_needed: str

    def __post_init__(self) -> None:
        if self.scheme not in SCHEMES:
            raise ValueError(f"unknown scheme {self.scheme!r}")


# ---------------------------------------------------------------------
# The one function permitted to decide what text represents an
# optional fact. Every renderer below reads facts through this (or
# `_facts_list`) exclusively.
# ---------------------------------------------------------------------

def _fact(value, formatter=str) -> str:
    """Return `UNKNOWN_MARKER` for `None`, an empty/blank string, or a
    falsy numeric zero-as-unset case is NOT special-cased here (0 is a
    real declared value, not absence) -- only `None` and blank strings
    are treated as absent. Never synthesises a substitute value."""
    if value is None:
        return UNKNOWN_MARKER
    if isinstance(value, str) and not value.strip():
        return UNKNOWN_MARKER
    return formatter(value)


def _facts_list(items: Tuple, empty_note: str) -> Tuple[str, ...]:
    """Render a tuple of already-structured facts (referees, skills) as
    lines, or a single explanatory line if the tuple is empty. Never
    pads a short list with an invented entry."""
    if not items:
        return (empty_note,)
    return tuple(str(i) for i in items)


# ---------------------------------------------------------------------
# Service-category mapping -- derived only from the operator's own
# declared `skills`, matched against the checklist's own verbatim
# category labels. A skill the operator did not declare is never
# matched to a category "because it's probably close enough."
# ---------------------------------------------------------------------

def _map_categories(skills: Tuple[str, ...]) -> Tuple[Tuple[str, str], ...]:
    lowered = tuple(s.lower() for s in skills)
    matches = []
    for code, label, keywords in _NSW_CATEGORY_K:
        if any(any(kw in s for s in lowered) for kw in keywords):
            matches.append((code, label))
    return tuple(matches)


# ---------------------------------------------------------------------
# Missing-facts checklists -- the highest-value output. Deterministic,
# derived only from what `SupplierDossier` actually carries.
# ---------------------------------------------------------------------

def _nsw_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    out = []
    if not d.facts.abn:
        out.append(MissingFact(
            "NSW_ICT_SERVICES_SCHEME", "ABN",
            "Supplier Hub profile cannot be created without an ABN "
            "(Scheme Rules: entities must have a current Supplier Hub "
            "profile before applying)."))
    if not d.facts.skills:
        out.append(MissingFact(
            "NSW_ICT_SERVICES_SCHEME", "declared service skills",
            "no skills declared -- cannot derive a Company Capacity "
            "and Capability narrative or a category (e.g. K03) match."))
    elif not _map_categories(d.facts.skills):
        out.append(MissingFact(
            "NSW_ICT_SERVICES_SCHEME", "a skill matching a Category K label",
            "declared skills do not match any Category K (Security "
            "management) label in the Scheme Rules -- confirm the "
            "correct category with buy.nsw before applying."))
    if len(d.facts.referees) < 2:
        out.append(MissingFact(
            "NSW_ICT_SERVICES_SCHEME", "two referee reports",
            f"Scheme Rules §8.1 requires two referee reports for the "
            f"nominated category; dossier carries "
            f"{len(d.facts.referees)}."))
    out.append(MissingFact(
        "NSW_ICT_SERVICES_SCHEME", "Supplier Declaration signature",
        "a standard authorisation/accuracy attestation -- this module "
        "never signs on the operator's behalf; the human must sign the "
        "real form."))
    out.append(MissingFact(
        "NSW_ICT_SERVICES_SCHEME", "financial solvency confirmation",
        "confirmation of solvency / no insolvency-or-ICAC proceedings "
        "is a legal declaration this module cannot make for the "
        "operator."))
    return tuple(out)


def _uk_ccs_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    out = [
        MissingFact(
            "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS",
            "DPS Schedule 1 filter category selection",
            "per LIVE_TARGET_REQUIREMENTS.md, the exact list of "
            "certification-free filters is not independently verified "
            "-- a human must read the real DPS Schedule 1 document "
            "before any filter is ticked; this module will not guess."),
        MissingFact(
            "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS",
            "Selection Questionnaire (SQ) financial details",
            "the SQ requires contact/financial details this dossier "
            "does not collect a UK-specific equivalent for."),
    ]
    if not d.facts.skills:
        out.append(MissingFact(
            "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS",
            "declared service skills",
            "no skills declared -- needed to identify which DPSQ "
            "service-type questions apply."))
    return tuple(out)


def _icn_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    out = []
    if not d.facts.abn:
        out.append(MissingFact(
            "ICN_GATEWAY", "ABN",
            "ICN Gateway auto-populates the profile from the ABR using "
            "the ABN at signup."))
    if not d.facts.skills:
        out.append(MissingFact(
            "ICN_GATEWAY", "declared service skills/keywords",
            "needed for the business summary and keyword/category "
            "fields (the FAQ notes the first sentence of the business "
            "summary is the most important)."))
    return tuple(out)


def _qld_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    out = []
    if not d.facts.skills:
        out.append(MissingFact(
            "QLD_SUPPLIER_PORTAL", "declared supply categories",
            "VendorPanel registration requires selecting supply "
            "categories before requesting invitation."))
    if not d.facts.business_address:
        out.append(MissingFact(
            "QLD_SUPPLIER_PORTAL", "business info / service regions",
            "registration completion requires business info and "
            "service regions."))
    return tuple(out)


def _irish_rail_7289_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    """Iarnrod Eireann CIE 7289 -- Qualification System for Penetration
    Testing. Open for applications before Jan 2029. Criteria quoted from
    the real PQQ (PQQ/CIE/Version/2/18)."""
    S = "IARNROD_EIREANN_7289_PENTEST"
    out = [
        MissingFact(S, "audited turnover of EUR 250,000/yr for 3 years, "
                    "OR a third-party reliance declaration",
                    "the ONLY Pass/Fail financial criterion: '5.1 MINIMUM "
                    "QUALIFICATION CRITERIA ... A minimum annual turnover "
                    "of 250k per annum for the last three audited "
                    "financial year ends.' The PQQ permits meeting this "
                    "with a third party's turnover ('Reliance on resources "
                    "to meet Turnover Requirement') -- if relying on a "
                    "partner, that entity's audited turnover and a signed "
                    "reliance declaration are required instead. Kyle must "
                    "supply his own figures or name a partner."),
        MissingFact(S, "Irish Tax Clearance Certificate obtainability",
                    "required at CONTRACT AWARD, not at application ('will "
                    "be required to be in possession of and produce a Tax "
                    "Clearance Certificate ... at time of contract award'). "
                    "Whether an Australian sole trader can obtain one from "
                    "the Revenue Commissioners has not been verified and "
                    "must be confirmed with Revenue before this route is "
                    "relied on. Does NOT block applying."),
        MissingFact(S, "signed PQQ minimum-qualification declaration",
                    "a signed Declaration in Part 2 of the Questionnaire "
                    "is a legal statement only the operator can make; this "
                    "module cannot sign for him."),
    ]
    if not d.facts.skills:
        out.append(MissingFact(
            S, "declared penetration-testing experience / references",
            "Technical & Professional Ability is SCORED (40% of points "
            "per criterion to pass), and client references are sought as "
            "feedback. No skills declared, so the scored section cannot "
            "be prepared. NOTE: insurance is DEFERRED to call-off and is "
            "NOT needed to apply."))
    return tuple(out)


def _gni_23_049_missing(d: SupplierDossier) -> Tuple[MissingFact, ...]:
    """Gas Networks Ireland 23/049 -- Qualification System for Cyber
    Security Services. Criteria quoted from the real QSQ."""
    S = "GAS_NETWORKS_IRELAND_23_049_CYBER"
    out = [
        MissingFact(S, "average annual turnover of EUR 175,000 "
                    "(pro-rata if recently established)",
                    "D1 Turnover (Pass/Fail): 'an average annual turnover, "
                    "in the last 2 years or pro-rata for a company "
                    "established within the last 2 years of at least: "
                    "EUR175,000.' Lowest financial bar found in Ireland. "
                    "Kyle must supply his own figures (pro-rata clause "
                    "helps a young business)."),
        MissingFact(S, "broker/insurer letter that cover CAN BE ARRANGED",
                    "F1 Insurance is satisfiable by a STATEMENT, not held "
                    "cover: 'provide a letter from their insurers/brokers "
                    "stating ... cover can be arranged' (PL EUR6.5m, PI "
                    "EUR6.5m, EL EUR13m, Products EUR6.5m). Kyle must "
                    "obtain such a letter -- he does not need to hold the "
                    "policies to apply."),
        MissingFact(S, "bank account in good standing (self-declaration)",
                    "the QSQ requires confirmation the company holds a "
                    "bank account presently in good standing -- a "
                    "declaration only the operator can make."),
    ]
    if not d.facts.skills and d.facts.years_experience is None:
        out.append(MissingFact(
            S, "cyber-security experience evidence (scored)",
            "Experience is scored 375 marks, 175 to pass, with an "
            "explicit carve-out: experience gained by an individual while "
            "working for a third-party entity CANNOT be relied upon. "
            "Kyle's own past employment does not count as his business's "
            "experience -- read this clause before spending effort here."))
    return tuple(out)


_SCHEME_MISSING_FNS = {
    "NSW_ICT_SERVICES_SCHEME": _nsw_missing,
    "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS": _uk_ccs_missing,
    "ICN_GATEWAY": _icn_missing,
    "QLD_SUPPLIER_PORTAL": _qld_missing,
    "IARNROD_EIREANN_7289_PENTEST": _irish_rail_7289_missing,
    "GAS_NETWORKS_IRELAND_23_049_CYBER": _gni_23_049_missing,
}


def missing_facts_for_scheme(dossier: SupplierDossier, scheme: str) -> Tuple[MissingFact, ...]:
    """The finite list of facts still missing before `scheme` can
    honestly be submitted for. Deterministic, derived only from what
    `dossier` carries -- never a guess at what the scheme "probably"
    wants beyond what the reference documents this module was built
    from actually state."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme {scheme!r}")
    return _SCHEME_MISSING_FNS[scheme](dossier)


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------

def _render_business_details(d: SupplierDossier) -> str:
    p, f = d.profile, d.facts
    lines = [
        "## 1. Business details",
        DRAFT_STAMP,
        "",
        f"- Business/trading name: {_fact(p.name)}",
        f"- ABN: {_fact(f.abn)}",
        f"- ACN: {_fact(f.acn)}",
        f"- Business address: {_fact(f.business_address)}",
        f"- Licence number: {_fact(f.licence_number)}",
        f"- Registration number: {_fact(f.registration_number)}",
        f"- Staff count (declared): {_fact(p.staff_count)}",
        f"- Languages worked in: {_fact(sorted(p.languages) or None, lambda v: ', '.join(v))}",
    ]
    return "\n".join(lines)


def _render_capability_statement(d: SupplierDossier) -> str:
    p, f = d.profile, d.facts
    lines = ["## 2. Capability statement", DRAFT_STAMP, ""]
    if not f.skills and not p.certifications and f.years_experience is None:
        lines.append(
            "No skills, certifications, or years of experience have "
            f"been declared. {UNKNOWN_MARKER}")
        return "\n".join(lines)
    if f.skills:
        lines.append(
            "Declared service capability: " + ", ".join(f.skills) + ".")
    else:
        lines.append(f"Declared service capability: {UNKNOWN_MARKER}")
    lines.append(f"Years of relevant experience: {_fact(f.years_experience)}")
    certs = sorted(p.certifications)
    lines.append(
        "Certifications held: " + (", ".join(certs) if certs else
                                    "none held — not applicable"))
    lines.append(f"Revenue band: {_fact(f.revenue_band)}")
    return "\n".join(lines)


def _render_category_mapping(d: SupplierDossier) -> str:
    matches = _map_categories(d.facts.skills)
    lines = ["## 3. Service-category mapping (NSW Category K — Security management)", DRAFT_STAMP, ""]
    if not matches:
        lines.append(
            f"No declared skill matched a Category K label. {UNKNOWN_MARKER}")
        return "\n".join(lines)
    for code, label in matches:
        lines.append(f"- {code}: {label}")
    return "\n".join(lines)


def _render_insurance(d: SupplierDossier) -> str:
    f = d.facts
    lines = ["## 4. Insurance", DRAFT_STAMP, ""]
    lines.append(
        f"- Professional indemnity cover (AUD): "
        f"{_fact(f.insurance_pi_cover_aud, lambda v: f'{v:,.2f}')}")
    lines.append(
        f"- Public liability cover (AUD): "
        f"{_fact(f.insurance_pl_cover_aud, lambda v: f'{v:,.2f}')}")
    lines.append(f"- Policy number: {_fact(f.insurance_policy_number)}")
    lines.append(
        "Note (NSW): insurance is not required to join the ICT "
        "Services Scheme, only to be in place before contracting "
        "(PBD 2023-03) — an absent figure above is not a blocker to "
        "applying.")
    return "\n".join(lines)


def _render_referees(d: SupplierDossier) -> str:
    refs = d.facts.referees
    lines = ["## 5. Referees", DRAFT_STAMP, ""]
    rendered = _facts_list(
        tuple(f"{r.name} ({r.organisation}) — {r.contact}" for r in refs),
        f"No referees declared. {UNKNOWN_MARKER}")
    for line in rendered:
        lines.append(f"- {line}")
    return "\n".join(lines)


def _render_standard_declarations() -> str:
    return "\n".join([
        "## 6. Standard compliance declarations",
        DRAFT_STAMP,
        "",
        "The following are legal declarations this module CANNOT make "
        "on the operator's behalf. Each renders as an action item, "
        "never a completed statement:",
        "",
        "- [ ] Confirm financially solvent, not subject to insolvency/"
        "ICAC proceedings, able to pay debts when due (operator to "
        "confirm and sign).",
        "- [ ] Agreement to use the applicable purchasing/commercial "
        "framework (operator to confirm and sign).",
        "- [ ] Supplier Declaration / accuracy attestation (operator to "
        "sign).",
        "- [ ] CCS Terms and Conditions acceptance (UK DPS — operator "
        "to accept electronically at the agreeing stage).",
    ])


def _render_missing_checklist(d: SupplierDossier) -> str:
    lines = ["## 7. Facts still missing before submission, by scheme", DRAFT_STAMP, ""]
    for scheme in SCHEMES:
        missing = missing_facts_for_scheme(d, scheme)
        lines.append(f"### {scheme}")
        if not missing:
            lines.append("No missing facts identified by this checklist.")
        else:
            for m in missing:
                lines.append(f"- {m.fact}: {m.why_needed}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_dossier(dossier: SupplierDossier) -> str:
    """Render `dossier` into the reusable answer set: capability
    statement, service-category mapping, standard questions, and the
    finite missing-facts checklist per scheme.

    Every section carries `DRAFT_STAMP`. This is preparation material a
    human transcribes into the real NSW Supplier Hub / UK SRS / ICN
    Gateway / QLD Supplier Portal forms and verifies before submitting
    -- it is never itself a submission, and it never completes a legal
    declaration on the operator's behalf.
    """
    if not isinstance(dossier, SupplierDossier):
        raise ValueError(
            f"render_dossier requires a SupplierDossier, got "
            f"{type(dossier).__name__}")

    sections = (
        f"# Supplier Registration Dossier — {DRAFT_STAMP}",
        "",
        "This document is preparation material only. It is not a "
        "submission. A human must transcribe, independently verify, "
        "and sign every declaration before anything here is submitted "
        "to NSW ICT Services Scheme, UK CCS Cyber Security Services 3 "
        "DPS, ICN Gateway, the QLD Supplier Portal, Iarnrod Eireann "
        "CIE 7289 (penetration testing), or Gas Networks Ireland 23/049 "
        "(cyber security).",
        "",
        _render_business_details(dossier),
        "",
        _render_capability_statement(dossier),
        "",
        _render_category_mapping(dossier),
        "",
        _render_insurance(dossier),
        "",
        _render_referees(dossier),
        "",
        _render_standard_declarations(),
        "",
        _render_missing_checklist(dossier),
    )
    return "\n".join(sections)
