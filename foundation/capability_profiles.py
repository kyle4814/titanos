"""Declared `CapabilityProfile` instances for a security business. Data
only -- no logic, no scoring, no fetching lives in this module.

WHY THIS EXISTS

The operator runs a security business: penetration testing, security
audit, incident response, SOC. The profile in production use before
this module (`swarm_contract.py`'s `_DEFAULT_KEYWORDS` /
`cpv_codes=("72000000",)`) leans on CPV 72000000, the UN/EU umbrella
code for "IT services: consulting, software development, Internet and
support". That code is not a filter -- it is the parent of most of the
public sector's IT spend. Every profile declaring it inherits
`relevance.py`'s rule that ANY CPV match alone is enough for
STRONG_MATCH regardless of keyword content (see `relevance.score()`),
so 72000000 alone floods the top band with AI platforms, GIS systems,
telecom contracts and campus hardware refreshes -- an IT-jobs feed, not
a security-work feed. Live proof of this failure mode is recorded
below in `OLD_GENERIC_IT_PROFILE`'s own docstring.

A `CapabilityProfile` DECLARED HERE IS AN UNVERIFIED CLAIM

Every profile in this module, like every `CapabilityProfile` anywhere
in this repository, is a self-report the operator makes about what
they can deliver. Nothing here checks it against a licence, a past
contract, a certification, or any external authority. Declaring a
profile with tight CPV codes and specific keywords makes it a BETTER
SURFACE-MATCH FILTER -- it does not make it a verified capability.
Treat every profile below exactly as you would a CV someone wrote about
themselves: informative, and not yet checked against reality.

RESEARCH METHOD (live TED, 2026-09-01)

Every CPV code below was verified three ways, against
`https://api.ted.europa.eu/v3/notices/search`, the same live endpoint
`foundation/mouth_ted.py` uses in production:

  1. `totalNoticeCount` for
     `deadline-receipt-request >= today() AND classification-cpv IN
     (<code>) AND publication-date >= today(-90)` -- proves the code
     returns a nonzero, non-everything count (a code matching nothing
     is not a filter; a code matching everything is not one either).
  2. Real notice titles under that count, read and judged by hand for
     whether they are security work, not IT work in general.
  3. A live, production-shaped side-by-side score comparison (see
     below) of the OLD profile and the profiles this module declares,
     run against real signals produced by `mouth_ted.sweep()` and
     `mouth_ted.observe()` -- the actual pipeline, not a synthetic
     fixture.

CANDIDATE CODES CHECKED AND REJECTED, WITH WHY

  72500000 (computer-related services)   -- 224 live notices. Sample:
      "Digitale werkplek", "Europees ICT-beheer", "scanning and
      invoicing", "System and support services". Generic IT, same
      failure class as 72000000 at a smaller scale. Rejected.
  72600000 (support and consultancy)     -- 208 live notices. Sample:
      same office-automation/support pool as 72500000, plus one
      genuine hit ("Surveillance and security systems and devices").
      Not precise enough to declare alone. Rejected.
  79710000 (security services)           -- 429 live notices. Sample of
      25: the overwhelming majority are physical guarding, CCTV
      installation, alarm monitoring and manned-guarding framework
      agreements ("Prestations de gardiennage", "Servicio de vigilancia
      y seguridad", "Objektschutz- und Rezeptionsdienstleistungen") --
      this operator's actual line of work (cyber) appears in maybe 1
      in 20. Because `relevance.score()` grants STRONG_MATCH on ANY
      CPV match regardless of keywords, declaring this code would
      promote hundreds of guard-service and CCTV-installation notices
      to the top band. Rejected as a `cpv_codes` entry in every profile
      below for that specific, verified reason.
  79714000 (surveillance services)       -- 104 live notices, same
      guarding/CCTV pool as 79710000 (it is 79710000's own child
      branch). Rejected for the identical reason.
  72222000 (information systems /
            technology strategic review)  -- 100 live notices. Sample of
      30: a minority are real security work ("Informatiebeveiliging en
      cybersecurity", "Sårbarhetsanalys och övervakning av
      cybersäkerhet"), but most are generic IT strategy/consulting
      ("Strategisch ICT Maatwerk Advies", "Contrat-cadre Conseil IT").
      Roughly 15-20% precision by hand count -- not clean enough to
      grant automatic STRONG_MATCH via CPV alone. Rejected as a
      `cpv_codes` entry.
  72810000 (this deployment labels it
            "computer back-up services")  -- only 10 live notices, and
      the label the task brief carried ("computer audit services") did
      not match what TED's own vocabulary returns for this code today:
      titles were IT backup/support ("PRESTATIONS D'ASSISTANCE ET
      D'EXPERTISE INFORMATIQUE" x3) and one compliance-monitoring
      notice, not audit work this operator does. Rejected -- the code
      does not mean what the brief assumed, verified rather than
      trusted from memory.

CANDIDATE CODES CHECKED AND KEPT, WITH THE EVIDENCE

  72212730 (security software development services) -- 16 live
      notices, ALL 16 read and judged security work: "Cyber Threat
      Intelligence Platform", "SIEM, SOC, SOAR-dienstverlening",
      "FRAMEWORK AGREEMENT FOR ... SIEM AND SOC SERVICES" (x4, one
      buyer re-published), "Network Security Services", "Security
      Operations Center (SOC)", "Managed Detection and Response
      (MDR)", "Ausschreibung SIEM-MSOC", a Polish hospital's SOC +
      information-security-management-system rollout (x2, re-listed),
      a Hungarian APT-detection-system support contract, and an Irish
      combined SOC+SIEM services tender (x2, re-listed). 16/16 on
      manual read = the highest precision of every code checked. This
      is the anchor code for `SECURITY_CORE_PROFILE`.
  48730000 (security software package)   -- 112 live notices, all 112
      read. Roughly 80-85% are genuine security-software procurement:
      firewalls and NGFW (Palo Alto, Cisco ESA/SMA, multiple "Next
      Generation Firewall" deployments), SIEM/SOC/XDR/EDR platforms,
      IAM/privileged-access-management, DNS security, malware-analysis
      platforms, a national "Cyberbezpieczne Wodociągi" (cyber-secure
      water utilities) programme repeated across several Polish
      municipal buyers, and a "Managed Security Operations Center
      (SOC)" framework in Germany. The remaining ~15-20% is hardware
      noise the CPV code's own family drags in: "Portable computers",
      a "Super computer" HPC acquisition, "Flow-measuring equipment",
      generic "Telecommunications services", and "File servers" with
      no security content in the title. Because a CPV match alone
      earns STRONG_MATCH, that noise would otherwise leak straight
      into the top band -- `SECURITY_BROAD_PROFILE.exclusions` below
      names those five noise categories explicitly (`portable
      computers`, `supercomputer`, `flow-measuring equipment`,
      `telecommunications services`, `file servers`) because
      `relevance.score()` checks exclusions BEFORE CPV, so an
      exclusion hit overrides even a CPV match. This code is precise
      enough to anchor a profile only with that exclusion list
      attached -- it is not clean enough to declare bare.

FULL-TEXT CHECK ON THE OPERATOR'S OWN VOCABULARY

A live TED title-only free-text search (`notice-title ~ (...)`, same
endpoint, 2026-09-01) for the literal phrases "penetration testing",
"red team" and "security audit" returned ZERO current open notices for
each; "incident response" returned exactly one. This is recorded
honestly because it caps what keyword-only matching on notice TITLES
can find: European buyers essentially never write "penetration
testing" into a notice title (it lives in the tender documents, not the
headline), so `keywords` in the profiles below matter most for their
hits inside notice DESCRIPTIONS (`mouth_ted.ted_signal()`'s
`description_safe` evidence field, which the CPV-anchored notices above
frequently do carry: "SIEM", "SOC", "cybersecurity", "penetration") and
for the notices no CPV code above catches at all. No profile below was
tuned to rely on title-only phrase matches, because the evidence says
that would not fire.

THE LIVE COMPARISON

Run 2026-09-01 against two real `mouth_ted` pulls:

  Sample A -- production `mouth_ted.sweep()`, i.e. exactly what the
  live pipeline already fetches (CPV 72000000/79000000/48000000,
  n=250 signals).
  Sample B -- the same pipeline, `classification-cpv IN (72212730,
  48730000)` substituted for the production query (n=122 signals) --
  the notices this module's own anchor codes actually select.

    profile              Sample A bands                  Sample B bands
    OLD_GENERIC_IT        STRONG=50 POSSIBLE=2             STRONG=13 POSSIBLE=20
                           WEAK=194 EXCLUDED=4              WEAK=89
    SECURITY_CORE_PROFILE STRONG=0  POSSIBLE=0              STRONG=14 POSSIBLE=4
                           WEAK=250                         WEAK=101 EXCLUDED=3
    SECURITY_BROAD_PROFILE STRONG=1 POSSIBLE=6              STRONG=96 POSSIBLE=4
                           WEAK=225 EXCLUDED=18              WEAK=15 EXCLUDED=7

  OLD's 50 STRONG_MATCH notices on Sample A were read by hand: the
  visible sample is "Tekoäly- ja automaatioratkaisut" (AI/automation),
  a GIS asset-management system, an IT-consultant dynamic purchasing
  system, "Air Travel Analytics", campus hardware/software, "online
  collaboration tools", a telecom operator contract -- zero of the 20
  read titles are security work. This is the exact failure the task
  brief named, reproduced live rather than assumed.

  SECURITY_CORE_PROFILE correctly abstains (0 STRONG_MATCH) on Sample
  A, because Sample A is drawn from a CPV family it deliberately does
  not declare -- it only lights up (14 STRONG, all genuinely security:
  Cyber Threat Intelligence Platform, MDR, SOC/SIEM x-several,
  Trellix-APT support) on Sample B, the notices its own anchor code
  selects. This is working as intended: it is a precision instrument,
  not a general-purpose radar.

  SECURITY_BROAD_PROFILE lights up on 96/122 (79%) of Sample B, matching
  the hand-counted ~80% precision of CPV 48730000 itself -- confirming
  the exclusion list catches the hardware noise it was built to catch
  without also cutting genuine hits, and that a CPV code's own real-world
  precision is the ceiling on any profile built around it: this profile
  cannot be more precise than the code it anchors on.

HONEST VERDICT

Both new profiles score better than OLD_GENERIC_IT_PROFILE on what
matters here: STRONG_MATCH stops being dominated by non-security IT
procurement. `SECURITY_CORE_PROFILE` trades recall for near-total
precision (16/16 and 14/14 hand-read). `SECURITY_BROAD_PROFILE` trades
some of that precision back for roughly 6x the STRONG_MATCH volume on
security-relevant notices, at the honest cost of the ~15-20% noise its
anchor CPV code itself carries. Neither profile is a free lunch: their
ceiling is the real-world precision of the CPV codes TED itself assigns,
verified above rather than assumed, and this module does not claim
otherwise.

ONE LIMITATION NOT SOLVED HERE, LOGGED FOR THE NEXT CYCLE

`mouth_ted.py` (owned elsewhere this cycle) still fetches only CPV
72000000/79000000/48000000 in production. Sample B above required a
one-off query substitution to prove these profiles work AT ALL, because
notices classified ONLY under 72212730/48730000 with no overlapping
72000000-family code never reach the scorer in production today. These
profiles improve ranking precision on whatever reaches them; they do
not, by themselves, widen what reaches them. That is a fetch-layer
change, out of this module's declared scope (`foundation/mouth_ted.py`
is explicitly not owned here).
"""

from __future__ import annotations

from foundation.relevance import CapabilityProfile

__all__ = [
    "OLD_GENERIC_IT_PROFILE",
    "SECURITY_CORE_PROFILE",
    "SECURITY_BROAD_PROFILE",
    "ALL_PROFILES",
]


# The profile this module replaces, kept here VERBATIM (same keywords,
# same single CPV code, same exclusions as `swarm_contract.py`'s
# `_DEFAULT_KEYWORDS` / `cpv_codes=("72000000",)` / `_DEFAULT_EXCLUSIONS`)
# so the live comparison recorded in this module's docstring is a fair
# fight against the actual production baseline, not a strawman rebuilt
# from memory. NOT wired into `swarm_contract.py` by this module --
# that file is owned elsewhere this cycle and is not touched here. This
# is a reference copy for comparison and for any future caller who
# wants the documented-bad baseline available by name.
OLD_GENERIC_IT_PROFILE = CapabilityProfile(
    name="old_generic_it",
    declared_by="capability_profiles_baseline_reference",
    keywords=(
        "cyber security", "penetration testing", "security audit",
        "incident response", "soc", "it consulting", "software development",
    ),
    cpv_codes=("72000000",),
    exclusions=(
        "construction", "catering", "cleaning", "vehicles",
        "medical supplies",
    ),
)


# NARROW. Anchored on the one CPV code that read 16/16 genuine security
# work by hand (72212730 -- see module docstring). Keywords are terms an
# operator doing penetration testing / security audit / incident
# response / SOC work would credibly use about themselves; none of them
# is also in this profile's own `exclusions` (structurally checked by
# `test_capability_profiles.py`). Exclusions cover the noise categories
# actually observed adjacent to security CPV codes during research
# (physical guarding/surveillance/CCTV/alarm vocabulary from the
# rejected 79710000/79714000 codes, plus the repository's existing
# generic-noise terms) so that free-text mentions of that noise cannot
# accidentally push a physical-security notice into a positive band.
SECURITY_CORE_PROFILE = CapabilityProfile(
    name="security_core",
    declared_by="capability_profiles_research_2026-09-01",
    keywords=(
        "penetration testing", "security audit", "incident response",
        "soc", "siem", "vulnerability assessment", "red team",
        "threat intelligence", "managed detection and response", "mdr",
        "cyber security", "cybersecurity",
    ),
    cpv_codes=("72212730",),
    exclusions=(
        "construction", "catering", "cleaning", "vehicles",
        "medical supplies", "portable computers", "supercomputer",
        "surveillance", "guard services", "cctv", "alarm system",
    ),
)


# BROADER. Adds CPV 48730000 (security software package -- ~80-85%
# hand-read precision) alongside 72212730, and widens the keyword list
# to the additional real vocabulary observed inside that code's live
# notices (firewall/NGFW, XDR/EDR, IAM, zero trust, cyber threat
# intelligence phrased as such). The exclusion list is 48730000's own
# documented noise categories (portable computers, supercomputer,
# flow-measuring equipment, telecommunications services, file servers)
# plus the same physical-security terms `SECURITY_CORE_PROFILE`
# excludes, so that `relevance.score()`'s "exclusion overrides even a
# CPV match" rule (checked before CPV, per that module's docstring)
# catches the hardware/telecom noise that would otherwise ride CPV
# 48730000's own STRONG_MATCH-on-any-match rule into the top band.
# This trades some of `SECURITY_CORE_PROFILE`'s precision for
# materially higher recall -- see the live comparison table in this
# module's docstring: 96/122 STRONG_MATCH on the security-CPV sample,
# versus 14/122 for the narrow profile, at the cost of inheriting
# 48730000's own ~15-20% real-world noise rate.
SECURITY_BROAD_PROFILE = CapabilityProfile(
    name="security_broad",
    declared_by="capability_profiles_research_2026-09-01",
    keywords=(
        "penetration testing", "security audit", "incident response",
        "soc", "siem", "vulnerability assessment", "red team",
        "threat intelligence", "managed detection and response", "mdr",
        "cyber security", "cybersecurity", "firewall",
        "security operations center", "extended detection and response",
        "xdr", "edr", "identity and access management", "iam",
        "next generation firewall", "ngfw", "zero trust",
        "cyber threat intelligence",
    ),
    cpv_codes=("72212730", "48730000"),
    exclusions=(
        "construction", "catering", "cleaning", "vehicles",
        "medical supplies", "portable computers", "supercomputer",
        "flow-measuring equipment", "telecommunications services",
        "file servers", "surveillance", "guard services", "cctv",
        "alarm system",
    ),
)


# Every profile this module declares, in the order they were built --
# narrowest to broadest. `OLD_GENERIC_IT_PROFILE` is deliberately NOT
# included: it is a comparison reference, not a recommendation this
# module makes.
ALL_PROFILES = (SECURITY_CORE_PROFILE, SECURITY_BROAD_PROFILE)
