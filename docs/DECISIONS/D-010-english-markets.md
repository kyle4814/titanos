# D-010 — English-language procurement markets beyond the first three

STATUS: ONE NEW MODULE BUILT (`foundation/mouth_find_a_tender_uk.py`),
seven other candidates recorded honestly (one blocked, six inconclusive/
not pursued this cycle — not fabricated as either working or dead).
DATE: 2026-09-02

## METHOD

Recon (robots.txt reads, homepage/search-page fetches, live query-
parameter tests) was done with plain `curl` (identifies itself as
`curl/8.5.0`, never a spoofed browser or search-engine User-Agent) and
`WebFetch`, exactly the same discipline `D-009-canada-access.md` used —
manual exploration, not a `foundation/mouth_common.py::fetch_feed()`
call, so no `DiscoveryPolicy` was spent on recon itself. Only the one
built module (`mouth_find_a_tender_uk.py`) calls `fetch_feed()`, gated by
its own `DiscoveryPolicy`. Every disallowed path was left unfetched;
where a `robots.txt` blocked us, only `robots.txt` itself was read.

## ROUTE 1 — Public Contracts Scotland (publiccontractsscotland.gov.uk) — BLOCKED

`robots.txt`, quoted in full:

```
User-agent: Googlebot
Disallow:
User-agent: Yahoo-slurp
Crawl-Delay: 1
Disallow:
User-Agent: bingbot
Crawl-Delay: 5
Disallow:
User-agent: Msnbot
Crawl-Delay: 1
Disallow:
User-agent: SemrushBot
Disallow: /
User-agent: SemrushBot-SA
Disallow: /
User-agent: *
Disallow: /
```

Four named search-engine bots are explicitly allowed; every other
user-agent, including this repository's own honest
`titanos-cosmic-library-mouth/1`, falls under the trailing
`User-agent: * / Disallow: /` and is blocked outright. This is the same
shape as AusTender and CanadaBuys — a real published rule, not a WAF
challenge — and the same refusal applies: evading it would mean
presenting a fabricated Googlebot/Bingbot identity, which this
repository's fetcher does not do. **NOT BUILT. Blocked by the site's own
declared policy.**

## ROUTE 2 — Sell2Wales (sell2wales.gov.wales) — RECON INCOMPLETE, NOT BUILT

`robots.txt` — HTTP 200, body is two bytes (`\r\n`): genuinely empty,
no directives at all, so nothing here is disallowed. The site itself
(`/Search/Search_MainPage.aspx`) is reachable (HTTP 200, distinct content
from a deliberately bogus path, so not a soft-404-everything server) but
renders its search results client-side; no `<form>`, `/api/` path, or
inline fetch call was found in the initial HTML, and the JS bundles that
would drive an XHR search were not reverse-engineered this cycle. An
"Export results (CSV)" style link was not found on this platform (unlike
UK Find a Tender's, see below). **NOT BUILT — genuinely reachable,
recon stopped short of finding a stateless GET endpoint; a real future
increment, not a dead end and not a working module either.**

## ROUTE 3 — eSourcing NI (etendersni.gov.uk) — RECON INCOMPLETE, NOT BUILT

`robots.txt` returns HTTP 302 (redirects to the homepage rather than
serving a text file) — read as "no robots.txt is published," same
conclusion as UK Find a Tender's HTTP 404, not a block. Runs the
"European Dynamics e-PPS" platform (`/epps/home.do`), the same platform
family as Ireland's eTenders and Malta's eTenders below.
`/epps/prepareCurrentOpportunities.do?currentType=cft` is reachable
(HTTP 200) but returns only a search-form-preparation page, not a
results list — the actual results almost certainly come from a
subsequent POST this cycle did not trace through. **NOT BUILT.**

## ROUTE 4 — UK Find a Tender Service (find-tender.service.gov.uk) — BUILT

`robots.txt` returns HTTP 404 with the site's own genuine "Page not
found" page (confirmed via `curl`, not a soft-404 — the app's own 404
template, not a blocking rule) — no robots.txt is published, nothing is
disallowed. See `foundation/mouth_find_a_tender_uk.py`'s own module
docstring for the full recon trail: reachable GET search endpoint
(`/search/opportunities`), a query parameter (`filters.cpv-codes`) that
demonstrably filters (200 results for CPV 79700000, 0 for a nonsense
code, 15,087 unfiltered — the first source in this repository's sweep
whose filter parameter is not silently ignored), and real live
security/cyber notices with real closing dates, e.g. "Ad-Hoc Application
Penetration Testing and IT Health Checks (PSN) and Other Security
Services," City of Bradford Metropolitan District Council, submission
deadline 14 September 2026,
`https://www.find-tender.service.gov.uk/procurement/ocds-h6vhtk-06e59c`.
**BUILT. `foundation/mouth_find_a_tender_uk.py` +
`foundation/tests/test_mouth_find_a_tender_uk.py`, 21 tests, all
passing, including a parse against the real captured live page (20/20
items parsed correctly, checked outside the test suite as a confidence
run, not committed as a test fixture).**

## ROUTE 5 — Ireland eTenders (etenders.gov.ie) — RECON INCOMPLETE, NOT BUILT

`robots.txt` returns HTTP 302 (redirects to homepage) — same "no
robots.txt published" reading as NI/Malta. Same European Dynamics e-PPS
platform, same `prepareCurrentOpportunities.do?currentType=cft`
form-preparation page reachable, same unresolved "what does the actual
results POST look like" gap. This is a DIFFERENT finding from the task
brief's prior pass, which found only a stale, non-commercially-licensed
bulk archive — this cycle found the live search UI is reachable but did
not trace it through to a working stateless GET. **NOT BUILT — genuinely
more promising than the prior pass's finding, still not a working
module.**

## ROUTE 6 — Jersey, Guernsey, Isle of Man — NOT ATTEMPTED THIS CYCLE

No recon was run against these three this cycle — deprioritised in
favour of finishing the UK Find a Tender build once it was found to
carry live security work, per this session's own Next-Lever Sequencer
(a proven high-value build in hand outranks starting three more
low-confidence recon passes in the same cycle). Recorded honestly as
unattempted, not as blocked or negative.

## ROUTE 7 — Malta (etenders.gov.mt) — RECON INCOMPLETE, NOT BUILT

`robots.txt` returns HTTP 302 (redirects to homepage). Same European
Dynamics e-PPS platform as NI/Ireland, same unresolved results-POST gap.
Malta is an EU member state with English as an official language,
confirmed from the reachable homepage content. **NOT BUILT — same
platform-family gap as routes 3 and 5; a future increment building one
parser for the shared "European Dynamics e-PPS results POST" shape would
likely unlock NI, Ireland and Malta together, not built separately this
cycle.**

## ROUTE 8 — UK university / NHS procurement portals — NOT ATTEMPTED THIS CYCLE

Not attempted — UK Find a Tender's own live results already surface NHS
England notices (e.g. "Penetration Testing Services 2026-2030," NHS
England, `ocds-h6vhtk-067639`) as a buyer within the CPV 79700000 filter,
so the marginal value of a separate NHS-specific portal recon this cycle
was judged lower than routes already found reachable. Individual
university procurement portals were not surveyed.

## OVERALL FINDING

| Route | robots.txt verdict | Reachable | Open-opportunity shape | Filter genuinely works | Live security work found |
|---|---|---|---|---|---|
| Public Contracts Scotland | blanket `Disallow: /` for `*` | NO | unknown | unknown | unknown |
| Sell2Wales | empty (fully permitted) | YES (page), search UI unresolved | unknown | not tested | not tested |
| eSourcing NI | no robots.txt published | YES (page), search UI unresolved | unknown | not tested | not tested |
| **UK Find a Tender** | **no robots.txt published** | **YES** | **YES — open opportunities with closing dates, confirmed live** | **YES — 200/0/15,087 result-count proof** | **YES — 4 named live notices, see module docstring** |
| Ireland eTenders | no robots.txt published | YES (page), search UI unresolved | unknown | not tested | not tested |
| Jersey/Guernsey/IoM | not attempted | — | — | — | — |
| Malta eTenders | no robots.txt published | YES (page), search UI unresolved | unknown | not tested | not tested |
| UK university/NHS | not attempted | — | — | — | — |

**One source cleared every check this cycle: UK Find a Tender Service.**
It is the post-Brexit TED-replacement for above-threshold UK public-
sector notices, genuinely open (not award-only), genuinely filterable,
and genuinely carries live, named, dated security/cyber work right now.
Public Contracts Scotland is a confirmed negative (robots-blocked, same
shape as AusTender/CanadaBuys). The four European-Dynamics-platform
sites (Sell2Wales, NI, Ireland, Malta) share one open, unresolved
question — what does their results-listing POST/GET actually look like
— which is a real, bounded next increment, not a dead end.

## ELIGIBILITY — WHAT WAS ACTUALLY CHECKED

Only checked for the one built source. UK Find a Tender's own Terms and
Conditions page carries no nationality/residency restriction. Individual
notices may still impose their own restriction; this module does not
read notice detail pages and so cannot confirm or rule that out per
notice — recorded as a genuine unknown in the module's own docstring,
not asserted either way.

## WHAT WOULD CHANGE THE UNRESOLVED ROUTES

- Sell2Wales / eSourcing NI / Ireland eTenders / Malta eTenders: trace
  the actual results-listing request (likely a POST from
  `prepareCurrentOpportunities.do` or a session-bound follow-up call) to
  find a stateless, keyless, GET-or-simple-POST shape
  `foundation/mouth_common.py::fetch_feed()` can call. If the shared
  "European Dynamics e-PPS" platform exposes the same shape on all four,
  one parser could plausibly serve all four with per-country `FEED_URL`
  constants — not assumed here, would need to be independently confirmed
  live on each host before being claimed.
- Jersey/Guernsey/Isle of Man, UK university/NHS portals: simply not
  attempted yet — first pass would be the same robots.txt + reachability
  + shape + filter-proof + live-notice sequence used for every other
  route in this document.

None of these five is a proven dead end. Public Contracts Scotland is
the one proven negative in this batch.
