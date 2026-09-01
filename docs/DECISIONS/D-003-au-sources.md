# D-003 — Australian public-sector opportunity source: none found

STATUS: DECISION RECORDED — NO MODULE BUILT.
AGENT: ENGINEER B, TITANOS cycle 003
DATE: 2026-09-01

## THE QUESTION

`foundation/tender_radar.py` (prior cycle) found no lawfully reachable
Australian government procurement source and used the UK Contracts
Finder OCDS API instead. This cycle's task: broaden the search beyond
the sources already ruled out there (AusTender, grants.gov.au,
data.gov.au, api.tenders.gov.au, and the five state tender portals) and
determine, independently and live, whether ANY Australian or
AU-relevant public-sector opportunity source is reachable by a fetcher
that identifies itself honestly (`titanos-cosmic-library-mouth/1
(+https://github.com/kyle4814/titanos)`), respects `robots.txt`, and
needs no authentication.

Conclusion: none. This document is the deliverable in place of a
module, per the same discipline `tender_radar.py`'s own docstring
uses — a real negative finding recorded precisely, not papered over,
and not manufactured into a build against a source that doesn't work.

## SOURCES TRIED, EACH VERIFIED LIVE 2026-09-01

Already ruled out by the prior cycle and not re-tried here: AusTender
(`tenders.gov.au`, `api.tenders.gov.au`), `grants.gov.au`,
`data.gov.au`, and `tenders.{nsw,vic,qld,wa,sa}.gov.au`. One check was
repeated in passing (`grants.gov.au/robots.txt` → HTTP 403 CloudFront,
same WAF block as before) purely to confirm nothing had changed; the
finding is unchanged and not claimed as new.

### State/territory open-data portals (separate hosts from `data.gov.au`)

| Host | robots.txt | Verdict |
|---|---|---|
| `data.nsw.gov.au` | HTTP 200, permissive for generic UA (Cloudflare content-signal block only names specific AI-crawler bots + a Drupal admin/search disallow list; `/api/` not disallowed) | reachable, but see "wrong shape" below |
| `data.sa.gov.au` | HTTP 200, same Drupal-generated disallow list, `/data/api/` not disallowed | reachable — API tested live |
| `data.vic.gov.au` | HTTP 301 (redirects; not independently checked further — lower priority once the shape problem below was confirmed) | not pursued |
| `data.qld.gov.au` | HTTP 301 | not pursued |
| `www.data.wa.gov.au` | HTTP 301 | not pursued |
| `data.brisbane.qld.gov.au` (CKAN/OpenDataSoft) | HTTP 200, but `Disallow: /api/` for `User-agent: *` (only `Googlebot` is allowed `/api/`) | **disallowed** — this fetcher is not Googlebot, honoured as written |
| `data.melbourne.vic.gov.au` (same platform) | identical `Disallow: /api/` for `*` | **disallowed** |

**Live test — `data.sa.gov.au`**: `GET
https://data.sa.gov.au/data/api/3/action/package_search?q=tender&rows=10`
→ HTTP 200, real CKAN JSON, `"count": 1543`. This is a genuinely open,
no-auth, robots-permitted, honestly-identified fetch that works.

**Why it is not used**: CKAN `package_search` returns *dataset
metadata* (title, publisher, resource files, format), not procurement
opportunities. The live query for `q=tender` returned dataset records
like `"Geothermal Tenements"` (a mining tenement dataset — "tenement"
matched "tender" as a substring, not a real hit), `"AusTender Contract
Notice Export"` (a static `.xls` file mirror of AusTender data from
2013, `datastore_active: false` on every resource — a dead historical
snapshot, not a live feed), and `"NSW e-Tendering"` (a dataset
*describing* the existence of the NSW portal, not the portal's live
contents). Forcing any of these into a `CanonicalSignal(kind="DEMAND")`
would mean reporting a buyer's current intent to purchase from a
record that has no buyer, no deadline, and in the AusTender case is
thirteen years stale. That is exactly the kind of value fabrication
`tender_radar.py`'s VALUE DISCIPLINE section forbids for its own
UK signals; the same discipline is applied here to not build at all
rather than build against the wrong shape of data. `data.nsw.gov.au`
was not queried directly given this finding already generalises to
"CKAN catalogue = dataset metadata, not opportunity notices" regardless
of which state's node answers it.

### Grants sources

| Host | robots.txt | Verdict |
|---|---|---|
| `business.gov.au` | HTTP 200, only disallows `/SearchResult` and `/*/Result` paths | reachable, no documented public API found |
| `www.communitygrants.gov.au` | HTTP 200, generic Drupal disallow list, nothing procurement-relevant blocked | reachable, no feed found |
| `grants.business.gov.au` | connection failed (curl exit, no response — host does not resolve/serve as a standalone endpoint) | unreachable |

`business.gov.au/grants-and-programs` (HTML page) returned HTTP 200.
Probing for a documented API (`/api/v1/grants`) returned an HTTP 302
Sitecore "page-not-found" redirect — not a real endpoint, a guess that
failed. No `<link rel="alternate" type="application/rss+xml">` or
documented machine-readable export was found on the grants listing
page. Reverse-engineering whatever private JSON endpoint the page's own
JavaScript calls was considered and rejected: this repository's
fetch discipline (see `mouth_common.py`) is to call documented,
intended-for-machine-consumption endpoints, not to inspect a page's
client-side network calls and treat an internal API as public just
because it is unauthenticated — that is a materially different kind of
access than a published OCDS/CKAN API with its own `help` field and
license statement.

### Council procurement SaaS platforms (VendorPanel, TenderLink, Apet360, eProcure)

These are named in the task brief as candidates because many AU
councils publish tenders through them. Tested at their public marketing
domains:

| Host | robots.txt | What's actually there |
|---|---|---|
| `www.vendorpanel.com.au` | HTTP 200, `Allow: /` | HTTP 302 redirect off the root — a marketing/login site, not a public tender listing. VendorPanel is multi-tenant; each council's tenders live behind that council's own tenant, not a shared public feed at this domain. |
| `www.eprocure.com.au` | HTTP 200, permissive except `crawl-delay: 10` | HTTP 302 redirect, same multi-tenant problem. |
| `www.apet360.com` / `apet360.com` | connection failed (no response within timeout) | unreachable |
| `tenders.net.au` (looked like a plausible AU tender aggregator domain) | HTTP 200 | **parked domain-for-sale page** — "This domain may be for sale," no tender content at all, ever |

**Structural finding, not per-host**: these platforms are multi-tenant
SaaS with no shared public listing surface — even where the vendor's
own marketing domain is reachable, an aggregate open feed across
councils does not exist at that domain. Reaching real tender data would
mean visiting individual councils' own tenant instances one at a time,
each a separate host with its own robots.txt to check and no guarantee
of a machine-readable feed (most present an HTML table, not RSS/Atom/
JSON) — checked directly on two real council tender pages below rather
than assumed.

### Individual council tender pages (spot-checked, not exhaustive)

| Host/page | Result |
|---|---|
| `cityofsydney.nsw.gov.au/business-opportunities-current-tenders` | HTTP 404 — guessed URL slug is wrong; the real page was not located within this cycle's time-box |
| `melbourne.vic.gov.au/.../current-tenders.aspx` | HTTP 403 — same WAF-class block pattern as the state portals |

No RSS/Atom `<link>` tag or feed URL was found on either page even
where reachable. Individual-council HTML scraping (as opposed to a
published feed) is out of scope for this module's shape by design —
`mouth_common.fetch_feed()` fetches one feed URL and parses structured
bytes; scraping an HTML table would require a second, bespoke parser
per council and no dedupe-safe identity field, and there is no single
feed that aggregates across councils to make that investment pay off
once.

### OCDS (Open Contracting Data Standard) in Australia

No Australian government body was found publishing under OCDS. The
Open Contracting Partnership's own implementer registry lists AusTender
as a *non-OCDS* system (its own proprietary schema, not the standard
`tenderPeriod`/`ocid`/`releases` shape `tender_radar.py` already
consumes from the UK). No AU host answering an OCDS-shaped endpoint was
found.

## FINDING

Two distinct failure modes account for every AU source tried, and they
are different from each other and worth keeping separate:

1. **Access blocked** (WAF/CloudFront 403, keyed API, blanket
   `robots.txt` disallow) — the same failure mode the prior cycle
   documented for AusTender/grants.gov.au/data.gov.au/state portals,
   and confirmed again here for the CKAN-catalogue `/api/` paths at the
   two council open-data portals that do run CKAN/OpenDataSoft
   (`data.brisbane.qld.gov.au`, `data.melbourne.vic.gov.au`).
2. **Access open but wrong shape** — a genuinely new finding this
   cycle: `data.sa.gov.au`'s CKAN API is real, live, lawful, and
   returns HTTP 200 with no authentication, but it answers "what
   datasets exist" not "what does a public body currently want to
   buy." No amount of query tuning turns a dataset catalogue into a
   procurement-notice feed; the underlying data isn't there. Grants and
   council-SaaS sources fall in a third bucket — reachable web pages
   with no documented machine-readable export at all, not even the
   wrong shape.

## IMPLICATION

The prior cycle's implication holds and is reinforced, not
contradicted: Australian public-sector *procurement notice* data is
not published anywhere this fetcher can lawfully reach, whether the
question is "is it blocked" (yes, everywhere it exists as real
notices) or "is it even the right kind of data" (no, everywhere it's
open). `tender_radar.py`'s UK OCDS source remains the one working
opportunity mouth in this repository.

## DECISION

No `tender_radar_au.py` is built. Building one against
`data.sa.gov.au`'s CKAN catalogue (the only genuinely open, no-auth,
robots-permitted candidate found) would mean emitting `DEMAND` signals
from dataset metadata with no buyer, no deadline and — in the one
concrete case checked — a thirteen-year-old static file, which is
fabrication of the exact kind this repository's value discipline
exists to prevent. A negative result, recorded precisely, is the
correct and complete output of this cycle.

## WHAT WOULD CHANGE THIS

- Any Australian government body begins publishing under OCDS, or
  publishes an AusTender/GrantConnect mirror through a host that
  doesn't sit behind the CloudFront WAF blocking non-browser
  User-Agents.
- A specific council's TenderLink/VendorPanel/Apet360 tenant instance
  is confirmed, live, to publish an actual RSS/Atom feed of current
  tenders (not the vendor's shared marketing domain) — this would still
  only cover one council, and the value of building `tender_radar_au.py`
  against a single-council feed versus the effort of confirming and
  maintaining it per council should be weighed explicitly before
  building, not assumed.
- `business.gov.au` or `communitygrants.gov.au` documents a public
  grants-listing API or feed (none was found by inspection of the
  reachable HTML in this cycle; not exhaustively verified against
  every path on either site).
