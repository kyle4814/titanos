# D-012 — European Dynamics e-PPS platform: Ireland cracked, NI/Malta not

STATUS: ONE NEW MODULE BUILT (`foundation/mouth_etenders_ie.py`), the
platform-wide "crack one, get four" hypothesis from
`docs/DECISIONS/D-010-english-markets.md` tested live and NOT confirmed.
DATE: 2026-09-02

## THE TASK

D-010 left four European Dynamics e-PPS platform sites (Sell2Wales,
eSourcing NI, Ireland eTenders, Malta eTenders) as "reachable, recon
incomplete" — none blocked by `robots.txt`, all sharing one unresolved
question: what does the actual results-listing request look like. This
cycle traced it for Ireland, the highest-priority candidate (English-
language, EU member, already the source of the only two English-
submission live notices found anywhere in the EU sweep plus the RTÉ
cyber DPS).

## METHOD

Recon done with plain `curl` identifying itself as
`titanos-cosmic-library-mouth/1` (this repository's own honest User-
Agent, never a spoofed browser or search-engine identity), same
discipline as D-010's own recon. `foundation/mouth_common.py::
fetch_feed()` was used only for the final build's own tests (via
injected `fetch_fn`, never the real network) and for one live
`DiscoveryPolicy`/`authorize_discovery()` composition check — the recon
itself, same as D-010, was manual exploration outside the gate.

## WHAT WAS FOUND — IRELAND (etenders.gov.ie)

`robots.txt` returns HTTP 302 (redirect to homepage, no robots.txt
published — same reading D-010 already gave this exact response).

The task brief's own hypothesis was a session-bound POST behind
`prepareCurrentOpportunities.do?currentType=cft`. **That hypothesis was
half right and half wrong.** The page IS session-bound for
search/sort/paginate — but it is NOT merely a form-preparation page as
D-010 recorded it. A completely fresh, cookie-less `curl` GET to
`https://www.etenders.gov.ie/epps/prepareCurrentOpportunities.do?currentType=cft`
returns HTTP 200 with the first page of the live "currently open CFT"
results table already embedded — real titles, contracting authorities,
publication dates, deadlines, procedure, status, and estimated value,
for whatever is open right now (2,916 total open CFTs at time of
writing). Two independent fresh fetches (no cookies, then with a cookie
jar) returned byte-identical `resourceId` sets — genuinely stateless,
not session reuse.

**Every filter/sort/paginate parameter tried was proven, live, to be
silently ignored** on this stateless GET — this task brief's own
fabrication-check discipline, applied and it caught a fifth instance of
the same failure class already seen in AusTender, World Bank,
Singapore, and NZ GETS:

| Parameter tried | Result |
|---|---|
| `freeText=security` vs `freeText=zzzznonsensequery9999` vs none | identical "2,916 results in total," identical row set |
| `d-3680175-p=2&searchType=cftFTS&latest=true` (the page's own "Next" link, copied verbatim) | identical 10 `resourceId`s as page 1 |
| `d-3680175-s=title.keyword&d-3680175-o=2` (the page's own column-sort link) | identical row order |
| `d-3680175-c=100`, `pageSize=100`, `rowsPerPage=100` (page-size guesses) | still exactly 10 rows |

The form's real POST target (`/epps/viewCFTSAction.do`, with
`isExport=true`) DOES exist, and reached through a real two-step session
(GET the search page for a cookie, then POST the same field set as an
ordinary HTML form — normal client behaviour, not a bypass, per this
task's own rules) returns a genuine live CSV-shaped export of the full
CFT dataset (confirmed live: 10,000 rows, 232 case-insensitive
`security`/`penetration`/`cyber` keyword hits in the raw text).
**This route is NOT used.** `mouth_common.py::fetch_feed()`'s `json_body`
parameter serialises a caller's mapping as a JSON request body with
`Content-Type: application/json` — confirmed live that this Java/
Struts-era form handler does not read a JSON body as form parameters:
POSTing it returns the plain search page, not the export, exactly as if
no body had been sent at all. Making this endpoint reachable would
require `mouth_common.py` to gain a form-urlencoded POST mode, which is
explicitly out of this cycle's file territory (`mouth_common.py` was on
the do-not-touch list) — a real, named, bounded future increment, not
worked around by hand-rolling a second socket.

No RSS/Atom feed, OCDS endpoint, or documented public API was found
anywhere in the homepage or search-page HTML (grepped case-insensitively
for `rss`/`atom`/`.xml`/`api/`/`ocds`/`feed`; the only hit was the plain
UI label "Export").

## WHAT THIS MEANS FOR THE BUILT MODULE

The only genuinely reachable, stateless, keyless, no-forged-identity GET
is the unfiltered first page of 10 live open CFT notices, in the
server's own default order (confirmed consistent across independent
fetches, not verified as a documented contract). `foundation/
mouth_etenders_ie.py` fetches that one page and filters CLIENT-SIDE, by
reading each item's own title/description against a small explicit
security/cyber/pentest keyword list — the same discipline
`mouth_gets_nz.py` already uses for a query parameter proven not to
work. Confirmed live against the real captured page, 2026-09-02: 10/10
rows parsed correctly; **zero of the current top-10 open CFTs are
security-relevant** — a real, honest, non-fabricated empty result for
this fetch window, not evidence the platform has no such notices (only
10 of 2,916 open CFTs are visible per fetch — see LIMIT below).

## WHAT WAS FOUND — NI AND MALTA (NOT CRACKED THIS CYCLE)

D-010's "crack one platform, likely crack all four" hypothesis is **NOT
confirmed**. Checked live, briefly, this cycle:
`https://www.etendersni.gov.uk/epps/prepareCurrentOpportunities.do?currentType=cft`
and
`https://www.etenders.gov.mt/epps/prepareCurrentOpportunities.do?currentType=cft`
both return a visibly different "Simple search" landing page (zero
`resourceId` matches, no "results in total" marker,
`<title>European Dynamics - Simple search</title>` /
`<title>Electronic Tendering - Simple search</title>`), not the
embedded-results shape Ireland returns on the identically-named
endpoint. The four sites are the same platform *vendor family*
(confirmed from `<title>`/branding text) but do NOT provably expose the
same results shape — each is a separate deployment configuration, and
this module makes no claim about NI, Malta, or Sell2Wales (Sell2Wales
was not re-tested this cycle; D-010's finding — client-side-rendered
search, no reachable endpoint found — stands unchanged).

## OVERALL FINDING

| Route | robots.txt | Reachable | Filter genuinely works | Live security work found this cycle |
|---|---|---|---|---|
| Ireland eTenders (`etenders.gov.ie`) | no robots.txt published | YES — page 1, 10 items, stateless | NO — every param silently ignored | NO — 0/10 in current window (honest empty result) |
| eSourcing NI (`etendersni.gov.uk`) | no robots.txt published | YES (form page only) | not tested — different shape | not tested |
| Malta eTenders (`etenders.gov.mt`) | no robots.txt published | YES (form page only) | not tested — different shape | not tested |
| Sell2Wales (`sell2wales.gov.wales`) | empty (fully permitted) | not re-tested this cycle | — | — |

**One source cleared "reachable, stateless, real live data": Ireland
eTenders.** It is genuinely built and tested, with a real, honest,
zero-count result for this fetch window — the module's own value is
proven capability (it CAN read live open Irish public-sector CFTs and
CAN flag security-relevant ones when they appear in the visible window),
not a claim of current live findings, which this cycle honestly has
none of.

## WHAT WOULD CHANGE THE UNRESOLVED ROUTES

- NI / Malta: repeat the exact recon this file just ran for Ireland
  (curl the `prepareCurrentOpportunities.do?currentType=cft` GET,
  inspect for an embedded results table vs. a bare search form; if a
  form, trace whatever the "Simple search" page's own submit target is)
  — not assumed to share Ireland's shape just because the platform
  vendor matches.
- Sell2Wales: still genuinely unresolved from D-010 — client-side
  rendering, no reachable endpoint found in that cycle's recon; not
  re-attempted here.
- The full CSV export (`viewCFTSAction.do`, `isExport=true`): would
  need `mouth_common.py::fetch_feed()` to gain a form-urlencoded POST
  mode (`Content-Type: application/x-www-form-urlencoded`, not the
  existing JSON-only `json_body`). A real, bounded, well-scoped future
  increment — the endpoint, session flow, and field list are already
  fully documented above, live-verified, and reusable the moment that
  capability exists. Would unlock full-dataset coverage (2,916+ open
  CFTs, not 10) rather than the current page-1-only window.

None of these three is a proven dead end.
