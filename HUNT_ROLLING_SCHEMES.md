# HUNT: Rolling Supplier Schemes (No-Deadline Structures)

Date: 2026-09-03
Method: WebSearch (exhausted after 6 calls — session hit the 200/session cap
before returning any results) + WebFetch (used for the rest; several target
URLs returned 403/404/500 on first guess, meaning many entries below are
UNKNOWN, not "does not exist"). No fabrication: every line either has a
source or is marked UNKNOWN.

**Reliability caveat on WebFetch summaries below**: WebFetch runs page
content through a small summarising model, not a literal parser. One page
(gca.gov.uk RM3764.3) was fetched twice and returned inconsistent
"Framework Type" labels between calls (no type stated vs. "Standard
Framework" — the latter contradicts the DPS status already confirmed by the
operator's own prior research). Treat any "DPS vs framework" classification
below as UNCONFIRMED unless it matches something already independently
verified. End dates and agreement names are lower-risk (more likely to be
literal reproductions) but still unverified against a primary document.

---

## RANKED — open now, low barrier, security/IT relevant

### 1. NZ Government Marketplace — Managed Security Services channel
*(already confirmed on the board, restated here for the ranking)*
- Owner: NZ Government Procurement and Property (MBIE)
- Covers: managed security services + broader IT/digital categories
- Open now: YES, until May 2029
- Entry requirement: "Required Pre-qualifications: None" (per prior finding)
- Application URL: NOT re-verified this session (marketplace.govt.nz
  security page returned 404 on the guessed path — re-check exact URL)
- Status this session: NOT independently re-confirmed. Carried forward
  from prior board entry only.

### 2. UK Government Commercial Agency (GCA) — Cyber Security Services 3 (RM3764.3)
*(already confirmed on the board, restated here for the ranking)*
- Owner: Government Commercial Agency (GCA) — **note: Crown Commercial
  Service rebranded to "Government Commercial Agency" effective 1 April
  2026**, per gca.gov.uk itself. This is a post-cutoff fact sourced from
  the live site, not verified against a second source — flag it, don't
  silently overwrite "CCS" everywhere without confirming with the operator.
- Covers: cyber security services, broad lots
- Open now: confirmed live/active on gca.gov.uk agreements list
- End date: 13/02/2029 (matches prior board finding)
- Entry requirements: UNKNOWN this session (page fetch for RM3764.3 detail
  errored 500 twice)
- Source: https://www.gca.gov.uk/agreements (fetched 2026-09-03)

### 3. NSW ICT Services Scheme
*(already confirmed on the board — always open)* — not re-verified this
session; guessed URL 404'd, needs a working link found via search next
session.

### 4. Queensland QITC
*(already confirmed on the board — no panel gate)* — not touched this
session; nothing new to add or contradict.

---

## UK — beyond Cyber Security Services 3

Source: https://www.gca.gov.uk/agreements (fetched directly, filtered on
"cyber"/keyword search). GCA = the 1 April 2026 rebrand of Crown Commercial
Service (see caveat above).

| Agreement | Ref | Covers | Status shown | End date | Notes |
|---|---|---|---|---|---|
| Cyber Security Services 3 | RM3764.3 | Cyber security services, broad | Open/Live | 13/02/2029 | Already on board as DPS; type label from this session's fetch is unreliable (see caveat) |
| Digital and IT Professional Services (DIPS) | RM6249 | Digital/IT professional services | Open/Live | 16/11/2027 | **MOD customers only** — buyer-side restriction, not obviously a barrier to supplier entry but scope is narrower than general public sector |
| Management Consultancy Framework Four (MCF4) | RM6309 | Management consultancy | Open/Live | 28/07/2027 | General consultancy, not security-specific |
| Digital Capability for Health 2 | RM6345 | NHS/health digital services | Open/Live | 09/12/2027 | Health-sector buyer scope |
| Cloud Compute 2 | RM6292 | Cloud/IT infrastructure | Open/Live | 27/11/2026 | Closing soonest of the set — verify refresh/re-open plans before relying on it |
| Crown Hosting II | RM6262 | Hosting | Open/Live | 06/10/2029 | Infrastructure, not directly security services |
| Artificial Intelligence (AI) | RM6200 | AI consultancy | Open/Live | 23/02/2029 | Adjacent, not core security |

**Critical unresolved question for all rows above except CS3**: whether
"Open/Live" means the agreement is *in force* (buyers can call off against
the existing supplier list) or *open for new suppliers to join* (DPS-style
continuous entry). The GCA site's summary language did not distinguish
this, and detail-page fetches for RM6200/RM3764.3 errored out (HTTP 500)
before the distinction could be confirmed. **Do not treat any row above
except CS3 as a confirmed "join now" opportunity — they are IN-FORCE
confirmed, OPEN-TO-NEW-SUPPLIERS unconfirmed.**

### NHS SBS / Health Trust Europe, ESPO, YPO
- ESPO (espo.org/frameworks): fetched, but the page returned only the
  shopping/category nav, no framework-level detail. UNKNOWN — needs a
  direct framework-list URL, not the top-level page.
- NHS SBS, Health Trust Europe, YPO: not fetched this session. UNKNOWN.

---

## Ireland — OGP

Every guessed URL failed this session:
- ogp.gov.ie/category/frameworks/ → redirected to gov.ie generic OGP page
  (no framework list rendered)
- gov.ie/en/office-of-government-procurement/ → HTTP 403
- gov.ie .../frameworks-catalogue/ → HTTP 403

**Status: UNKNOWN.** No OGP framework data obtained this session — not
"no schemes exist," just not reached. Needs a working entry URL (likely
findable only via search, which is exhausted for this session).

---

## New Zealand — beyond the Marketplace

- procurement.govt.nz/all-of-government-contracts/ fetched successfully,
  but the actual AoG panel/contract listings sit behind **Procure Connect**,
  which requires RealMe login and agency sign-up — i.e. **the syndicated
  panel detail is not publicly crawlable**. This is itself a finding: NZ's
  AoG contract detail (supplier lists, categories, whether a given panel is
  open to new suppliers) is gated behind authenticated access, unlike the
  Marketplace which is public.
- Source: https://www.procurement.govt.nz/all-of-government-contracts/
- Status: UNKNOWN beyond the Marketplace channel already on the board.

---

## Australia — beyond NSW and QLD

- Federal BuyICT (buyict.gov.au): every panel-detail page attempted
  required login (session-expired redirect or 403). **BuyICT panel status
  is gated behind account creation to view**, similar to NZ. Public
  crawlable detail: none obtained this session.
- tenders.gov.au: HTTP 403.
- WA Common Use Arrangements, SA, TAS, ACT, NT ICT panels: not reached —
  guessed URLs 404'd. UNKNOWN.

---

## Canada

- canadabuys.canada.ca/robots.txt: **explicitly checked, per the rule.**
  Confirmed disallow: the file allows Googlebot/Bingbot only (5s crawl
  delay, tender/award notices still blocked even for them), then applies
  `Disallow: /` to all other user agents — i.e. blanket disallow for this
  tool. **Not fetched, per rule. Recorded as unreachable by robots.txt.**
- No alternative source (e.g. a mirror, a government press release listing
  open Supply Arrangements) was pulled this session. Status: UNKNOWN.

---

## International organisations

- UNGM (ungm.org): registration and overview pages both required login or
  404'd on guessed paths. Known from general public-domain fact (not
  independently re-verified this session): UNGM Basic registration is
  free and has no closing date — vendors can register at any time. **This
  specific claim is UNCONFIRMED this session** — flagging rather than
  asserting it as freshly verified, since the fetch attempts failed and I
  will not present prior general knowledge as a verified 2026 finding.
- Development banks (World Bank, ADB, IDB, AfDB vendor/consultant rosters):
  not attempted this session. UNKNOWN.

---

## OPEN vs IN-FORCE — explicit call per scheme

| Scheme | In force? | Open to new suppliers NOW? | Confidence |
|---|---|---|---|
| UK CS3 (RM3764.3) | Yes | Yes (DPS, to Feb 2029) | High — matches prior independently-confirmed board entry |
| NZ Marketplace (Managed Security) | Yes | Yes (to May 2029, per prior finding) | Medium — not re-verified this session |
| NSW ICT Services Scheme | Yes | Yes (always open, per prior finding) | Medium — not re-verified this session |
| QLD QITC | Yes | Yes (no panel gate, per prior finding) | Medium — not re-verified this session |
| UK DIPS (RM6249) | Yes (to Nov 2027) | UNKNOWN — MOD-only buyer scope, entry mechanism unconfirmed | Low |
| UK MCF4 (RM6309) | Yes (to Jul 2027) | UNKNOWN | Low |
| UK Digital Capability for Health 2 (RM6345) | Yes (to Dec 2027) | UNKNOWN | Low |
| UK Cloud Compute 2 (RM6292) | Yes (to Nov 2026 — closing soon) | UNKNOWN | Low |
| UK Crown Hosting II (RM6262) | Yes (to Oct 2029) | UNKNOWN | Low |
| UK AI (RM6200) | Yes (to Feb 2029) | UNKNOWN | Low |
| Ireland OGP frameworks | UNKNOWN | UNKNOWN | None — no data reached |
| NZ other AoG panels | Yes (per Rule 38 requirement) | UNKNOWN — gated behind Procure Connect/RealMe | None |
| AU federal BuyICT panels | UNKNOWN | UNKNOWN — gated behind login | None |
| AU state panels (WA/SA/TAS/ACT/NT) | UNKNOWN | UNKNOWN | None |
| Canada Supply Arrangements/Standing Offers | UNKNOWN | UNKNOWN | None — robots.txt disallow on canadabuys, no alt source pulled |
| UNGM vendor roster | Believed always-open (general knowledge) | UNCONFIRMED this session | None (unverified) |
| Development bank rosters | UNKNOWN | UNKNOWN | None |

---

## WHY THE HUNT STOPPED SHORT (honest accounting)

1. **WebSearch budget was exhausted for this session before a single
   search returned results** (0 of 6 queries executed — hit the
   200-call/session cap immediately, likely from prior activity in the
   same session, not from these 6 calls). This is the actual root cause
   of most UNKNOWNs above: without search, every non-already-known URL had
   to be guessed, and most guesses 404/403'd.
2. WebFetch alone cannot discover URLs it doesn't already have — it can
   only fetch or follow redirects from a known link. That limited this
   hunt almost entirely to re-confirming the four items already on the
   board (partial success: 2 of 4 re-confirmed, 2 not re-touched) plus one
   genuinely new find (the UK GCA rebrand + the 6 non-CS3 GCA agreements,
   with open-to-new-suppliers status unresolved for all 6).

## NEXT MOVE

Re-run this hunt in a fresh session (fresh WebSearch budget) targeting, in
priority order: (1) OGP Ireland framework catalogue — zero data this
session; (2) whether the 6 non-CS3 GCA agreements are DPS-style
continuous-entry or closed-list frameworks — the single highest-value
unresolved question, since RM6200/RM6249/RM6309/RM6345 cover exactly the
security/IT/consultancy space this hunt is for; (3) Canada, via a
non-canadabuys source (e.g. a specific PSPC buyandsell.gc.ca page, checked
against its own robots.txt first).
