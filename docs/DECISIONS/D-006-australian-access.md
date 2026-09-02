# D-006 — Australian public-sector opportunity source: still none. A
# reachable adjacent market (NZ GETS) was found instead.

STATUS: DECISION RECORDED — ONE MODULE BUILT (`mouth_gets_nz.py`, not
`mouth_austender.py` — see naming note below).
AGENT: ENGINEER B, TITANOS cycle 016
DATE: 2026-09-02

## THE QUESTION

The operator is an Australian cyber-security business (pen testing,
security audit, incident response, SOC) that needs Australian
government and public-sector work — same language, same jurisdiction,
no cross-border barriers, local presence. Two prior cycles
(`tender_radar.py`'s own module docstring, `docs/DECISIONS/
D-003-au-sources.md`) already found every direct Australian government
procurement route blocked or wrong-shape. This cycle's job: find routes
NOT yet tried — bulk/CDN-hosted AusTender exports, state RSS/OCDS
feeds, council SaaS tenants, universities/health services, lawful
aggregators, and a New Zealand equivalent (GETS) as a realistic
adjacent market.

## NAMING NOTE — WHY THIS FILE ISN'T `mouth_austender.py`

The task brief for this cycle asked for `foundation/mouth_austender.py`
specifically, presupposing an Australian source would be found. One was
not. What WAS found and built is `foundation/mouth_gets_nz.py`, reading
New Zealand's GETS feed — the task brief's own item 6 named this
candidate explicitly. Naming a module that emits NZ signals
`mouth_austender.py` would mislabel every signal it produces as
Australian, the identical defect `mouth_ted.py`'s own docstring already
refuses for EU notices mislabelled "UK". See `foundation/mouth_gets_nz.py`'s
own module docstring for the full reasoning.

## ROUTES TRIED THIS CYCLE, EACH VERIFIED LIVE 2026-09-01/02

Already ruled out by D-003 and not re-tried: AusTender's own search/
Atom/Report paths (still HTTP 403, CloudFront WAF, reconfirmed once in
passing), `grants.gov.au`, `data.gov.au`, `api.tenders.gov.au`, the five
state portals, `data.brisbane.qld.gov.au`/`data.melbourne.vic.gov.au`
(CKAN `Disallow: /api/` for `*`), `business.gov.au`/
`communitygrants.gov.au` (no documented feed), council SaaS marketing
domains (VendorPanel/eProcure — multi-tenant, no shared listing).

### 1. AusTender bulk/CDN-hosted dataset — genuinely reachable, wrong shape (confirmed on a fresher file)

| Host | robots.txt | Verdict |
|---|---|---|
| `data.open-contracting.org` | HTTP 200, `Disallow:` empty | reachable, no auth |
| `fastly.data.open-contracting.org` (the actual file CDN) | HTTP 200, `Disallow:` empty | reachable, no auth |

The Open Contracting Partnership's own registry (`/en/publication/19`)
mirrors AusTender data as real OCDS JSON/CSV/XLSX, "retrieved monthly,"
last-modified 2026-08-14 — far more current than D-003's stale 2013
CKAN snapshot. Downloaded `2026.jsonl.gz` live (16.9MB compressed,
103MB uncompressed, 50,269 records) and inspected directly, not
assumed: **50,269/50,269 (100%) already carry an `awards` array; 0/50,269
have a `tender.tenderPeriod` field.** This is contract-AWARD data
(decided, signed contracts with real supplier/buyer/amount fields), not
open-opportunity data. Emitting a `DEMAND` signal from it would report
an already-awarded contract as something the operator could still bid
on — the same fabrication class D-003's own "wrong shape" finding
already ruled out, reconfirmed here on a fresher file rather than
assumed to still hold. **NOT USED.**

Licence: CC BY 3.0 AU — noted for the record in case a future cycle
finds a legitimate use for AU award/competitive-intelligence data
(e.g. "which suppliers are winning security-relevant AU government
work" as a distinct, honestly-labelled signal type, not a bid
opportunity). Not built this cycle — out of this cycle's scope and a
different signal shape than `DEMAND`.

### 2. NZ open-data catalogue (`catalogue.data.govt.nz`) — same wrong shape

| Host | robots.txt | Verdict |
|---|---|---|
| `catalogue.data.govt.nz` | HTTP 200, `Disallow: /api/` for `*` | API path disallowed, same shape as `data.gov.au` |

The one matching dataset found by title search (a page-level HTML
fetch, not the disallowed `/api/` path) is titled "New Zealand
Government procurement **award** notices" — CSV exports on
`www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/`. Same wrong
shape as #1: award data, not open opportunities. **NOT USED.**

### 3. NZ GETS (Government Electronic Tenders Service) — REACHABLE, RIGHT SHAPE

| Host | robots.txt | Verdict |
|---|---|---|
| `gets.govt.nz` (redirects to `www.gets.govt.nz`) | HTTP 200, disallows only `SEMrushBot`/`SemrushBot`/`SemrushBot-SA` | fully reachable for this fetcher's honest User-Agent |

`https://www.gets.govt.nz/ExternalRSSFeed.htm` is a real, live RSS 2.0
feed titled "GETS Open Tenders or Quotes" — "This feed list the current
open tenders or requests for quote listed on the GETS." Fetched live
2026-09-02: **337 `<item>` entries**, no key, no login. Most recent
`pubDate` 2026-08-26 (six days before this cycle's date); earliest item
a 2021 standing panel still genuinely open. Real organisations present
include HEALTHNZ, Ministry of Justice, MFAT, MSD, several district
councils, and Aurora Energy (a lines company that also tenders through
GETS). Categories are real UNSPSC codes including
`92121700 - Security systems services`, `84111600 - Audit services`,
`81110000 - Computer services`.

**Filter-fabrication check, as required by this cycle's task brief**:
`?category=`, `?region=`, and `?classificationId=81110000` were each
appended to the feed URL and compared against the bare URL. All four
requests returned the identical 337-item feed, byte-for-byte item
count — an unrecognised query parameter is silently accepted and
ignored, not honoured. `mouth_gets_nz.py` does **not** attempt
server-side filtering; it fetches the one full feed and reads each
notice's own `<category>` tags client-side, same discipline
`tender_radar.py`'s own CANNOT section documents for Contracts
Finder's CPV parameter.

`www.gets.govt.nz/api` returns HTTP 401 (keyed) — not used; the RSS
feed above needs no key and was preferred.

**USED. Built `foundation/mouth_gets_nz.py` + `foundation/tests/
test_mouth_gets_nz.py` (25 tests, all passing, including a live
sanity check against the real 337-item feed captured 2026-09-02).**

### 4. NZ OCDS

`ocds.nz` does not resolve (DNS failure, `curl` exit 6). MBIE's own
stated commitment to adopt OCDS for GETS (per public search results) is
not yet implemented as a queryable endpoint this fetcher could find.
Not pursued further this cycle.

## VALUE SHAPE OF `mouth_gets_nz.py`'s OWN OUTPUT

Every signal is `kind="DEMAND"`, `pressure_class="EXPLICIT_DEMAND"`,
`source_type="OFFICIAL"`. `money_state` is **always** `NOT_OBSERVED` —
confirmed live: no `<item>` in the 337-entry feed carries a structured
value/amount field anywhere in the RSS envelope; mentions of "value" or
"$" appear only inside free-text descriptions ("no maximum value has
been set") and are never parsed into a number. See the module's own
docstring for the full discipline.

## FINDING

Two distinct failure modes account for every AU/NZ source tried this
cycle, matching D-003's own two-bucket framing exactly:

1. **Access blocked or wrong shape for Australia specifically** —
   AusTender's live web endpoints remain WAF-blocked; the one genuinely
   reachable, genuinely current AU dataset (the OCP registry mirror) is
   award data, not opportunity data, the same "right host, wrong shape"
   problem D-003 first found on a 13-year-old file and this cycle
   reconfirms on a 19-day-old one.
2. **NZ is different**: GETS is reachable, unblocked, unauthenticated,
   and the right shape (open tenders, not awards) — the operator's
   realistic adjacent market, exactly as this cycle's task brief's item
   6 anticipated.

## DECISION

No `mouth_austender.py` is built — Australian government procurement
remains genuinely unreachable in the right shape, same conclusion as
D-003, now checked against a fresher AusTender data source and a
second, NZ-side catalogue with the identical wrong-shape defect.
`foundation/mouth_gets_nz.py` is built instead: the operator's home
market (Australia) still has no lawful, correctly-shaped opportunity
feed this fetcher can reach; the adjacent market (New Zealand) does,
and this cycle produces the repository's first real external ping into
that market — 337 live, open NZ government tenders reachable right now,
several in security-relevant UNSPSC categories.

## WHAT WOULD CHANGE THIS

- AusTender or any AU state/territory body begins publishing OPEN
  (not-yet-awarded) tender notices through a host not sitting behind
  the CloudFront/Azure WAF class this fetcher cannot lawfully evade.
- MBIE's own stated GETS-OCDS integration commitment (found via web
  search, not yet independently verified as a live endpoint) ships a
  real queryable OCDS surface for GETS — would let a future cycle
  cross-check `mouth_gets_nz.py`'s RSS-scraped fields against a
  structured API rather than the current HTML-table-regex recovery for
  `close_date`/`rfx_id`.
- A specific Australian council's TenderLink/VendorPanel/Apet360 tenant
  is confirmed, live, to publish an actual RSS/Atom feed of current
  tenders — still a per-council decision to make explicitly (see
  D-003's own note on this), not assumed to generalise.
