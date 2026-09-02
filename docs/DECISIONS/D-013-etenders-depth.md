# D-013 — Ireland eTenders: page-1-only was a wrong URL, not a wall

STATUS: PAGINATION FIX BUILT AND TESTED (`foundation/mouth_etenders_ie.py`).
`D-012`'s "pagination is silently ignored" finding was re-tested and found
FALSE — it tested the wrong URL. TED-Ireland coverage measured to
quantify what the below-threshold half of eTenders is worth relative to
what TED already gives us for free.
DATE: 2026-09-02

## THE TASK

`mouth_etenders_ie.py` (built earlier the same day, `D-012`) reached only
page 1 of eTenders' 2,916 open Call for Tenders — 10 notices, 0 of them
security-relevant in that window. The task: find a legitimate route past
page 1 without a session, without spoofing anything, and without adding
cookie/session state to `mouth_common.py` (that's a real security
decision on the repo's only socket, out of scope for this cycle). If
none exists, quantify what TED alone already covers for Ireland so the
size of the real gap is known rather than assumed.

## RE-EXAMINING D-012'S "PAGINATION IS IGNORED" FINDING

D-012 appended `d-3680175-p=2&searchType=cftFTS&latest=true` (copied
verbatim from the page's own "Next" link) to
`prepareCurrentOpportunities.do?currentType=cft` and got page 1 back
again, every time — concluding pagination needs a session this stateless
fetch doesn't carry.

That conclusion doesn't survive re-testing. Confirmed live, 2026-09-02:

```
GET /epps/prepareCurrentOpportunities.do?currentType=cft
-> HTTP/1.1 302 Found
   Location: /epps/quickSearchAction.do?searchType=cftFTS&latest=true
```

`prepareCurrentOpportunities.do` is not the results page. It is a
redirect that always lands on page 1 of `quickSearchAction.do`, no
matter what query string is appended to the prepare URL — which is
exactly why D-012's test always got page 1 back: it never reached the
real results endpoint at all.

Re-run against `quickSearchAction.do` directly (the redirect *target*,
not the prepare page), `d-3680175-p=N` is genuinely honoured, statelessly:

| Test | Result |
|---|---|
| `d-3680175-p=1` fetched twice, no cookies | byte-identical `resourceId` sets both times — confirmed stateless |
| `d-3680175-p=1` vs `d-3680175-p=2` | **zero overlap** in `resourceId` sets |
| `d-3680175-p=2` vs `d-3680175-p=3` | zero overlap |
| `d-3680175-p=99999` (nonsense) | distinct "No results" shape — no `<table id="T01">`, no "results in total" marker, not a repeat of page 1 |
| `d-3680175-p=293` (one past the real last page, 2,916 CFTs / 10 per page = 292 pages) | same honest "No results" shape as the nonsense value |
| `d-3680175-p=292` (the real last page) | 7 rows (2,916 − 291×10 = 6, close to the 7 observed — page counts drift slightly between fetches as new notices publish, expected) |
| `d-3680175-c=100` (page-size), same endpoint | **still silently ignored** — confirmed unchanged, still exactly 10 rows regardless of value |

This is exactly the fabrication-check discipline this task brief asked
for: a genuinely ignored parameter returns identical content for any
value (this is what page-size still does, and what pagination
*appeared* to do against the wrong URL); a genuinely honoured one
returns distinct, deterministic content per value with a well-formed,
distinguishable end-of-data signal past the real end — which is what
pagination against the *right* URL actually does.

**No session, no cookie, no forged identity was used or needed to prove
any of this.** Two independent fetches — one with zero cookies, one with
a full cookie jar from a prior request in the same run — returned
byte-identical results at every page tested. `robots.txt` still returns
HTTP 302 (no robots.txt published, same reading D-010/D-012 already
gave). Sorting parameters were not re-tested this cycle (out of scope —
pagination was the blocking finding to correct; sorting doesn't change
*how much* is reachable, only the order).

## WHAT WAS BUILT

`foundation/mouth_etenders_ie.py`:

- `RESULTS_URL` — the real endpoint (`quickSearchAction.do?searchType=
  cftFTS&latest=true`), replacing the redirect-only `prepareCurrentOpportunities.do`
  as the module's target.
- `_page_url(page)` — builds `RESULTS_URL&d-3680175-p={page}`.
- `_fetch_pages(policy, max_pages)` — walks pages 1..`max_pages`, one
  `fetch_feed()` call per page (so authorization and budget are charged
  per page, not once for the whole walk), stopping the moment a page
  carries no `<tbody>` — the honest "past the last page" signal, not an
  error.
- `_merge_pages_html(pages_raw)` — concatenates the `<tbody>` content of
  every fetched page into one synthetic document so `parse_items()`
  (unchanged) still just parses `<tr>` blocks. Never fabricates a
  "results in total" marker: if no fetched page carried a recognisable
  marker, none is added, so `parse_items()`'s existing "no rows AND no
  marker -> FetchError" rule still fires on a genuinely unrecognised
  page shape instead of that case being silently read as an honest
  empty result.
- `MAX_PAGES = 20` — a deliberate courtesy bound, not a platform limit.
  The platform was proven above to honour every page up to the real end
  of ~292. Twenty was chosen so one cron tick issues at most 20
  sequential requests against a public government server, not ~292 —
  raising it later costs nothing structurally if that courtesy limit
  turns out to be too conservative once this runs for real.
- `DISCOVERY_POLICY.max_queries` set to `MAX_PAGES` (was the single-digit
  default) — one full sweep is now the budget unit this bounds, since
  one sweep now makes up to `MAX_PAGES` real requests, not one.

`foundation/mouth_common.py`, `hunt.py`, `sources.py` — **not touched**,
per file territory. `form_body` (added 2026-09-01, the same capability
`mouth_ted.py`'s POST needed) was available to reach for here but wasn't
needed: the pagination fix is a GET with a different query string, not a
form submission.

## TESTED

30/30 tests in `foundation/tests/test_mouth_etenders_ie.py`, offline
(mocked `urllib.request.urlopen`, no real network in the suite),
including two new end-to-end proofs added this cycle:

- `test_default_observe_path_walks_multiple_pages_until_honest_end` —
  mocked pages 1 and 2 each carry a real row, page 3 returns the exact
  "No results" shape confirmed live; asserts the sweep collects both
  real rows and stops at page 3 (3 requests, not `MAX_PAGES`).
- `test_default_observe_path_refuses_once_budget_is_exhausted` (updated)
  — budget set to exactly `MAX_PAGES`; first sweep spends it in full
  (mock always returns a page with a `<tbody>`, so `_fetch_pages()` walks
  the complete `MAX_PAGES` before stopping), second sweep's first request
  is refused.

Full 8-subsystem regression run in progress at the time of writing this
document; result to be appended once it completes (see NEXT below if it
surfaces anything).

## LIVE MEASUREMENT: WHAT THE FIX ACTUALLY BUYS

A real, honest, non-fabricated sample — 30 pages (300 open CFT notices,
~10% of the 2,916 open at fetch time) — fetched live 2026-09-02 and run
through this module's own `is_security_relevant()` keyword list:

**11 of 300 (3.7%) matched.** Real, not all false positives — several
are genuinely security/cyber-relevant:

- Security Operations Centre (SOC), SIEM and Managed Incident Response
  (IR) Service
- 0055 - The Provision of Security Operations Centre (SOC) and Security
  Information and Event Management (SIEM) Services
- Request for Tenders for the Provision of Managed Security Services
- Cybersecurity Specialist Services
- PQQ for the Provision of Managed Services to support a national Public
  Key Infrastructure (PKI) including physical security devices

The rest of the 11 are the module's own documented false-positive class
(the bare word "security" appearing incidentally in an unrelated
tender — a playgrounds framework, a website redevelopment, an internal
communications platform) — named honestly here rather than folded into
the headline count.

**Before this fix: 0 of 10 (the whole D-012 fetch window) were
security-relevant.** After: a real, live, non-zero, multi-item result
reachable statelessly, with no session and no forged identity — the
concrete deliverable this task asked for. Extrapolated (not measured
directly) across the full 2,916 open CFTs at the observed 3.7% rate:
roughly 100+ security-relevant notices exist in the platform right now;
`MAX_PAGES=20` (200 notices/sweep) will surface a rotating ~7 of them
per sweep at that rate, not all ~100 in one run — the honest bound
this document's own CANNOT section states plainly.

## TED-IRELAND COVERAGE — HOW MUCH OF THIS GAP TED ALREADY CLOSES

Queried live 2026-09-02 against `mouth_ted.py`'s already-working
endpoint (`api.ted.europa.eu/v3/notices/search`, POST, no key):

| Query | `totalNoticeCount` |
|---|---|
| `deadline-receipt-request >= today() AND buyer-country IN (IRL)` | **746** |
| ... AND `classification-cpv IN (72000000, 79000000, 48000000)` (IT/software/business-services CPV families) | **225** |

TED only carries **above-threshold** notices (the EU-wide publication
requirement). eTenders' 2,916 open CFTs cover both above- and
below-threshold Irish procurement. So: TED already gives us 746 of
whatever above-threshold slice of those 2,916 exists; the remainder —
roughly 2,170 notices, i.e. most of the platform — is specifically the
**below-threshold** tier TED structurally cannot see, because it is
never obligated to be published there. That is the real, quantified size
of the gap this eTenders fix closes that TED does not already close:
not "2,916 notices we'd otherwise miss," but "the below-threshold ~75%
of Irish public procurement, which is invisible to TED by design, not by
any fetcher limitation."

This means the eTenders fix is not redundant with the already-working
TED module — it reaches a genuinely different, non-overlapping slice of
Irish demand (smaller contracts, more Irish-SME-reachable, structurally
excluded from the EU-wide feed). Both modules should keep running; they
are not competing for the same notices.

## WHAT WOULD IMPROVE THIS FURTHER (not built this cycle)

- **Raise `MAX_PAGES` beyond 20** once this runs for real for a while
  and the courtesy-vs-coverage tradeoff can be judged on real cron
  history rather than guessed up front. No code change needed beyond
  the constant and the matching `DISCOVERY_POLICY.max_queries`.
- **The CSV export (`viewCFTSAction.do`, `isExport=true`, 10,000 rows,
  232 keyword hits across a broader dataset than just currently-open
  CFTs)** remains genuinely blocked, and this cycle did not change that
  status. `mouth_common.fetch_feed()` gained `form_body` on 2026-09-01
  specifically for TED, and it's tempting to assume that's what was
  missing here too — **it is not.** The established, task-brief-supplied
  fact stands: this endpoint returns HTTP 500 without a session cookie,
  independent of body encoding. `form_body` lets a caller send the right
  *content type*; it does nothing about the missing *session*. Making
  this endpoint reachable needs one of:
  - A cookie jar / session-carrying mode added to `fetch_feed()` —
    genuinely two-step (GET the search page for a `Set-Cookie`, carry
    that cookie on the following POST) — which is real session/identity
    state on the repository's only socket, and is deliberately **not**
    proposed as code here. It is a real security decision (what does
    "this fetcher now has a notion of a session" mean for every other
    caller of `fetch_feed()`, not just this one?) that belongs to
    whoever owns `mouth_common.py`'s threat model, not to a single
    mouth's file territory.
  - If that mode is ever built, the security implications worth naming
    up front: a session-carrying fetcher can be tricked into carrying an
    attacker-supplied cookie across requests if the cookie source isn't
    pinned to the same authorized `DiscoveryPolicy`/URL; a cookie is
    also a small but real piece of per-target state that outlives a
    single request, which is a new category of thing for
    `fetch_feed()`'s "one function, no session, no retry loop" design
    to reason about; and a fetcher that can hold a session looks a lot
    closer to "logging in" than "reading a public page," which is the
    exact line `HUMAN_DECISIONS.md`'s standing discovery authorization
    (READ_URL/READ_API, no login-required systems) was written to keep
    clear. None of this is a reason not to build it — it is the reason
    it should be a deliberate, reviewed increment, not a side effect of
    fixing eTenders' pagination.
- Sorting (`d-3680175-s=...`) was not re-tested against `quickSearchAction.do`
  this cycle. Worth a quick check if a future cycle wants deterministic
  ordering (e.g. deadline-soonest-first) rather than the platform's
  default order — low priority, since pagination alone already delivers
  the coverage gain this task asked for.

## OVERALL FINDING

D-012's "page 1 only" conclusion was a real, honestly-reported result at
the time — but it was reported against the wrong URL, and this cycle's
own re-examination (exactly what the task brief asked for: "test each
candidate against a nonsense value to confirm the parameter is actually
honoured before believing it") caught that. The corrected, tested,
30/30-green result: eTenders IE now reaches up to `MAX_PAGES` × 10 = 200
open CFTs per sweep, statelessly, with no session and no forged
identity — a genuine, quantified, non-zero increase in reachable Irish
security-relevant procurement, and a documented, named path (session
cookies) for the one piece that remains genuinely blocked.
