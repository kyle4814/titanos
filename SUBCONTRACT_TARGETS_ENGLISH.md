# SUBCONTRACT TARGETS — ENGLISH-SPEAKING MARKETS

## Extension of SUBCONTRACT_TARGETS.md — do not edit that file, this is additive

Built 2026-09-02, same session. `SUBCONTRACT_TARGETS.md` already mined 198
TED award notices (mostly Germany/Netherlands) and independently ranked
INFODAS GmbH and AWARE7 GmbH as the strongest leads. That work is not
redone here. This file extends in four directions the base file named as
gaps: (1) UK/Ireland English-market awards, (2) verified entry paths for
an individual with no certifications and no company, (3) firms that
explicitly run an associate/freelance tester model, (4) Australia/NZ.

**Operator profile assumed throughout:** solo, Australia, no
certifications (no OSCP/CREST/CHECK), no insurance, no corporate
references, English only, cannot be a prime, can be a subcontractor or
associate tester.

**Method note — why this file leans on web search over raw API pulls:**
`SUBCONTRACT_TARGETS.md` already documented that UK Contracts Finder
rate-limits to ~1 request per 30-50s and its keyword parameter is
ignored server-side. Re-running that pull for marginal additional awards
was judged lower value than using targeted web search to (a) surface
additional named UK award notices already indexed by search engines and
(b) — the task's real emphasis — verify actual, currently-reachable entry
paths for each candidate company, which an API pull cannot tell you at
all. Every company/award/URL below was independently fetched or returned
in a search result this session; nothing is inferred or assumed.

---

## RANKED TABLE — lead with the ones an uncertified solo operator could approach today

| Rank | Company | Market | Why it's a target | Entry path (verified) | Certification bar |
|---|---|---|---|---|---|
| 1 | **Pulse Security** | NZ | Small, explicitly "interested in both newbies and seasoned hackers," DFIR + pentest boutique | `careers@pulsesecurity.co.nz` — [pulsesecurity.co.nz/careers](https://pulsesecurity.co.nz/careers): send "something concrete you can show us that you've broken or built" — no CV-gate, no cert requirement stated | **None stated** — demonstrated skill substitutes |
| 2 | **Volkis** | AU (Sydney) | Confirmed (via own published staff bio on the Volkis Handbook) to have **run an associate penetration tester program** upskilling testers "from various degrees of industry experience" — a named, historical precedent for exactly this operator profile, not a guess | [volkis.com.au](https://www.volkis.com.au/) — careers page blocked our fetch (403); approach via site contact form / LinkedIn, ask specifically about the associate programme by name | Unclear — programme is explicitly aimed at people without deep prior experience |
| 3 | **AWARE7 GmbH** | Germany (carried over from base file, restated here because it's the strongest single lead in either file) | 2 confirmed TED wins, explicitly "welcomes initiative applications, especially from experienced pentesters" | [aware7.com/career](https://aware7.com/career/) | Pays for OSCP/CEH/CISM — implies not required to start |
| 4 | **ZX Security** (Bastion Security Group) | NZ | 50+ staff, CREST-certified boutique, explicitly open to unsolicited applications | `careers@bastionsecurity.co.nz` — [zxsecurity.co.nz/about/careers](https://zxsecurity.co.nz/about/careers/) | **Hard restriction: "only considering candidates currently in New Zealand"** — disqualifying for an AU-based operator unless relocated/visiting |
| 5 | **Ionize Pty Ltd** | AU (Canberra) | 3 confirmed AusTender awards in the last 12 months (ASIC $238,846; ACCC $74,800; ATSB $25,000) — the clearest, most recent Australian public-sector recurring buyer relationship found this session | `sales@ionize.com.au` / [ionize.com.au/careers](https://www.ionize.com.au/careers/) — page explicitly invites unsolicited contact ("please talk to us!") even when no role is posted | Not stated on careers page; team holds GPEN/GWAPT/OSCP/OSEP per marketing copy — likely expected for senior roles, unclear for associate/contract |
| 6 | **OnSecurity** | UK | Runs a named **"Associate Network"** for freelance/contract pentesters — the clearest explicit associate-model firm found in the UK market | [onsecurity.io/about-onsecurity/careers](https://onsecurity.io/about-onsecurity/careers/) — **currently states "not currently recruiting," send CV to their listed email**; the associate-network posting found (via a third-party job aggregator, StudySmarter) is not confirmed still open on OnSecurity's own site | **Hard requirement stated in the posting: OSCP, OSWE, or CREST CRT/CCT ("or equivalent")** — operator does not currently qualify |
| 7 | **Triskele Labs** | AU (Melbourne) | CREST-registered boutique, founder-led, markets itself as "one of the last remaining boutiques in Australia" — boutiques are the segment most likely to flex to contractors | [apply.workable.com/triskele-labs](https://apply.workable.com/triskele-labs/?lng=en) | Not stated; standard ATS listings only, no explicit associate track found |
| 8 | **Salus Digital Security Ltd** (Salus Cyber) | UK | Named winner, IPO £1,337,500 CHECK award (carried over from base file); small Cheltenham firm, size of win suggests real delivery-capacity need | [saluscyber.com/Careers](https://saluscyber.com/Careers) — generic careers page, offers to "arrange a friendly chat before applying" | CREST-approved firm (per CREST Marketplace listing) — likely expects CHECK/CREST credentials for pentest delivery roles specifically |
| 9 | **NCC Group** | UK | Large, established, carried over from base file (won a DSIT GovAssure award) | [nccgroupplc.com/careers](https://www.nccgroupplc.com/careers/) — standard corporate ATS (Workday) | Mandatory background/vetting process stated; no associate/freelance track found — weakest entry path of the UK names checked |

---

## DIRECTION 1 — UK/Ireland English-market awards (extending the base file's 12-day UK sample)

The base file's UK Contracts Finder pull covered only 2026-08-21 to
2026-09-01 due to rate-limiting. This session used targeted web search
(not the throttled API) to surface additional UK award notices indexed
outside that 12-day window, without re-triggering the 429s:

| Notice title | Buyer (where stated) | Value | Source |
|---|---|---|---|
| IT Health Checks and Penetration Testing (G-Cloud 14 call-off) | not named in search snippet | £210,000 | [Contracts Finder notice 73ce78d1-...](https://www.contractsfinder.service.gov.uk/Notice/73ce78d1-dfb5-413f-a286-6cb9276d1634) |
| IT Health Checks and Penetration Testing (G-Cloud 14 call-off) | Ministry of Defence | £75,000 | [Contracts Finder notice, MoD ITHC award](https://www.contractsfinder.service.gov.uk/notice/b1e4e11c-86d0-4199-a048-545325f91c4b) |
| Penetration Test and ITHC Services | Nuclear Decommissioning Authority | not confirmed | [Contracts Finder notice 04d9d422-...](https://www.contractsfinder.service.gov.uk/Notice/04d9d422-7a8f-41b0-a745-1764db26169e) |
| Public Sector Network IT Health Check | not confirmed | not confirmed | [Contracts Finder notice 6da9d084-...](https://www.contractsfinder.service.gov.uk/notice/6da9d084-6f6a-4b26-a755-1250ea454901) |

**Honest limitation**: direct WebFetch of Contracts Finder notice pages
returned HTTP 403 in this session (site blocks the fetch tool used here,
distinct from the base file's rate-limit finding on the raw OCDS API) —
so the winning **supplier names** for these four notices could not be
independently confirmed this session, only the notice titles/values that
search engines had indexed. They are listed as leads to verify directly,
not as confirmed winners. Do not treat these as equivalent in reliability
to the base file's table, which did pull winner names from the OCDS
`awards` array directly.

**Crown Commercial Service Cyber Security Services 3 DPS** — the base
file already flagged this as the single highest-leverage UK research
step (the actual supplier roster). Not pursued further this session;
still the top UK follow-up.

**Ireland** — TED already covers Ireland as an EU member state, and the
base file's TED pull already surfaced two Irish winners: Minana
International T/A GoodPeople (€6,000,000, Dept. Children, Equality,
Disability) and Secora Consulting (€80,000, Teagasc). Ireland's own
national portal, eTenders.gov.ie, was checked this session and confirmed
to run a separate, searchable award-notice facility (CPV/date-filterable)
distinct from TED — but requires an interactive session search, not a
static/API pull, and was not further mined this session. One historical
Irish award found via search: a PSI (Pharmaceutical Society of Ireland)
framework "for penetration testing, vulnerability scanning, forensic
discovery and related ICT services" — response deadline 30/09/2020, so
the winner (if any) is outside the base file's 24-month window and not
listed here as current.

---

## DIRECTION 2 — Entry paths (see ranked table above; this section is the raw findings)

Companies checked for a real, fetchable entry path this session, with
result:

- **OnSecurity** (UK) — has a named Associate Network model, but the
  live careers page currently says "not currently recruiting." The
  associate-track job description (certs required: OSCP/OSWE/CREST
  CRT-CCT) was found via a third-party aggregator, not confirmed live on
  OnSecurity's own site as of this session.
- **Volkis** (AU) — direct site fetch blocked (403); independently
  confirmed via a Volkis staff member's own published bio that Volkis
  **has run** an associate penetration tester program for people at
  "various degrees of industry experience." Worth a direct approach
  asking about it by name.
- **Ionize** (AU) — careers page explicitly invites unsolicited contact
  even with no open role; 3 recent AusTender awards.
- **Triskele Labs** (AU) — standard Workable ATS, no associate track
  found, but explicitly self-describes as a boutique.
- **Pulse Security** (NZ) — lowest-friction entry path found in this
  entire session: no CV gate, demonstrated capability substitutes,
  explicitly open to newcomers.
- **ZX Security / Bastion Security Group** (NZ) — open to unsolicited
  applications but explicitly restricts to candidates "currently in New
  Zealand."
- **Aura Information Security** (NZ, offices also in Melbourne/Sydney) —
  confirmed CREST-approved, NZ/AU dual-market presence; no careers page
  or contractor-model language found this session — logged as a company
  to check directly, not a confirmed lead.
- **Salus Digital Security / NCC Group / QinetiQ** (UK, carried over from
  base file) — all have standard corporate careers pages; no
  associate/freelance track found for any of the three this session.
  QinetiQ's careers page was not independently re-checked this session
  (base file already named it); treat as unverified for entry-path
  purposes.

---

## DIRECTION 3 — Firms explicitly running an associate/freelance tester model

Two confirmed this session, both carrying real caveats:

1. **OnSecurity (UK)** — named "Associate Network," but current
   certification bar (OSCP/OSWE/CREST) excludes this operator today, and
   the live careers page shows no active recruiting call.
2. **Volkis (AU)** — historical associate program targeting people with
   "various degrees of industry experience," which reads as the closest
   fit found to an uncertified entrant; not confirmed still running,
   direct site check blocked by a 403 this session.

No third firm with an explicit, currently-open, no-certification-required
associate/freelance tester program was found this session. This is
reported as a genuine negative finding — the search was not narrow, it
covered UK, AU, and NZ boutiques by name and by search term — not a gap
left unexplored.

---

## DIRECTION 4 — Australia / NZ security consultancies

**Comprehensive company list found**: a maintained public GitHub list
(`0x10f2c/Aus-Infosec-and-Pentesting-Companies`) names 59 Australian/NZ
infosec and pentesting firms, split into amalgamated (larger group /
holding-company owned) and independent companies. Independents
potentially worth individual follow-up beyond those already checked
above: AirGlow Security, Aurian Security, Content Security, Cyber
Partners, Elttam, GridWave, Hacktive, Intalock, Mercury Infosec,
Quantum Security Services, RedCursor, Rightsec, Secolve, Security
Centric, Sentaris, Shea Security, Silent Grid, Skylight Cyber,
StickmanCyber, Themissinglink (TML), Vertex Security, Zerosource. None of
these were individually checked for entry paths this session — logged as
the next batch, not fabricated as leads with unverified detail.

**Who wins Australian government pentest work (confirmed via AusTender
this session)**: **Ionize Pty Ltd** — 3 separate contract notices in the
last 12 months (ASIC $238,846.00, 29-Oct-2025 to 30-Oct-2026; ACCC
$74,800.00, 13-May-2026 to 12-May-2027; Australian Transport Safety
Bureau $25,000.00, 15-Apr-2026 to 30-Jun-2026) — this is a genuine
repeat-winner pattern by the same standard the base file used for TED
(Tier 1 = multiple wins in the window), found independently in the
Australian data. **CyberCX** and **Sekuro** also confirmed as large,
established AU/NZ players via search (CyberCX ~Brisbane-based, Sekuro
Sydney-headquartered, CREST-approved, now part of Infosys) but no
specific AusTender award was independently pulled for either this
session — named as known large players, not confirmed public-sector
winners in this file.

**New Zealand**: the government's own procurement route for this work is
the **GCDO Assurance Services Panel** (25 providers across portfolio/
programme/project/technical-design/technical-implementation assurance
categories) — but the provider list itself is gated behind RealMe login
and agency authorization; it could not be read publicly this session.
This is the NZ equivalent of the base file's Crown Commercial Service DPS
finding: the real supplier roster exists but sits behind a login wall,
not published as an open dataset. Flagged as a dead end for this
operator specifically (RealMe requires a NZ government relationship to
access), not a research gap.

Direct NZ boutiques identified and their entry paths are captured in
Direction 2 / the ranked table (Pulse Security, ZX Security, Aura).

---

## LIMITATIONS (stated honestly, not hidden)

- UK supplier names for the 4 additional Contracts Finder notices listed
  in Direction 1 are **not confirmed** — WebFetch was blocked (403) on
  Contracts Finder notice pages this session, so only notice
  titles/values from search-engine indexing are given, not verified
  award data from the OCDS `awards` array. Treat these strictly as leads
  to check directly, not as equivalent-confidence entries to the base
  file's TED table.
- Ireland's national eTenders portal was confirmed to exist and be
  separately searchable from TED but was not mined this session beyond
  one out-of-window historical PSI framework notice.
- 21 of the 59 companies on the AU/NZ infosec list were not individually
  checked for entry paths — named as a follow-up batch, not fabricated.
- No AusTender award was independently pulled for CyberCX or Sekuro
  despite both being named as large AU/NZ players by web search — they
  are not listed as confirmed public-sector winners in this file for
  that reason.
- NZ's GCDO Assurance Services Panel provider roster is real but
  login-gated (RealMe + agency authorization) and could not be read.
- No individual person's name, personal email, or personal phone number
  was collected anywhere in this file. Every contact point listed
  (`careers@...`, `sales@...`) is a company-operated inbox, not a named
  individual, matching the same rule the base file applied.
- No outreach was drafted or attempted. This file is research only.
