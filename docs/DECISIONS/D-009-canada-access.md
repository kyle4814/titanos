# D-009 — Canada procurement data: no permitted route found

STATUS: DECISION RECORDED — NO NEW MODULE BUILT. The canadabuys.canada.ca
block from prior discussion stands; no legitimate route around it exists.
DATE: 2026-09-02

## METHOD

No fetches were made through `foundation/mouth_common.py::fetch_feed()`
(no `DiscoveryPolicy` was authorized for this recon; this was manual
`WebFetch` exploration of robots.txt/licence/API text only, not a
repository-code network call). No spoofed User-Agent, no path disallowed
for us was fetched — where robots.txt blocked a host, only the
robots.txt itself was read, never the disallowed content.

## ROUTE 1 — open.canada.ca (Open Government Portal / CKAN)

`https://open.canada.ca/robots.txt` — HTTP 200, real text file:

> `User-agent: *` / `Crawl-delay: 20`, disallows `/admin/`, `/search/`,
> `/user/login` etc., `/profile`, table-sort query paths. **No mention
> of `/data/` or the CKAN API paths anywhere.** This host is reachable
> for us.

The CanadaBuys tender-notices dataset **is** mirrored here as a
registered CKAN package (id `6abd20d4-7a1c-4b38-baa2-9525d0bb2fd2`,
"CanadaBuys tender notices"). `package_show` returned 12 resources
(New/Open/2026-2027/.../2009-2022 tender notices, data dictionary,
supporting docs). **Every single resource has `datastore_active:
false`.** CKAN's own metadata record does not hold the row data — it
holds a pointer. Every resource's `url` field is a direct link back to
`canadabuys.canada.ca/opendata/pub/*.csv` — the exact host and path
already ruled disallowed (robots.txt: named `Allow` rules for
Bingbot/Googlebot only, then a blanket `User-agent: * / Disallow: /`,
`Crawl-delay: 5`, no `/opendata/` carve-out — re-verified this cycle,
unchanged from the prior finding). A `datastore_search` call against one
of the resource ids (`5870de7c-86fe-4d05-8d73-cd412e12fdeb`, "Open
tender notices") returned HTTP 404 — confirms no queryable copy of the
actual rows exists inside CKAN's own datastore on the permitted host.

**Finding: open.canada.ca is reachable, but reachable only to metadata
that repoints to the disallowed host. It is not an independent copy of
the data — it is a directory entry for the same blocked door.** Fetching
the CSV via the link found on open.canada.ca is still an HTTP GET to
`canadabuys.canada.ca`, governed by that host's own robots.txt regardless
of where the URL was discovered. This route does not clear the block.

## ROUTE 2 — Official CanadaBuys API

`https://canadabuys.canada.ca/en/procurement-and-contracting-data`
describes only two things: bulk CSV/data-file downloads (the same
`opendata/pub/*.csv` files, same blocked host) and the OCDS pilot
("machine readable JSON file" — see Route 4). **No REST/SOAP API is
described anywhere on this page.** `open.canada.ca/en/access-our-
application-programming-interface-api` documents the generic CKAN
action API (GET-only) for *open.canada.ca's own registry* — not a
CanadaBuys-specific endpoint, and it only ever returns metadata for this
dataset (Route 1). No documented terms-of-use grant exists for
programmatic access to the live tender rows themselves. **No API with a
real access grant exists for the data we need.**

## ROUTE 3 — Open Government Licence – Canada

`open.canada.ca/en/open-government-licence-canada`, quoted directly:

> "You are free to: **Copy, modify, publish, translate, adapt,
> distribute or otherwise use the Information in any medium, mode or
> format for any lawful purpose.**" Grants a "worldwide, royalty-free,
> perpetual, non-exclusive licence... including for commercial
> purposes," conditioned only on attribution ("Contains information
> licensed under the Open Government Licence – Canada.").

This licence is genuinely permissive and would clear all *downstream
reuse* concerns if the data were in hand. **It does not touch access
control.** A licence governs what you may do with information once
lawfully obtained; it says nothing about how to obtain it, and does not
override a robots.txt directive at the host serving the file. This is
the same distinction already drawn for AusTender in prior decisions —
licence permissiveness cannot substitute for a reachable, permitted
fetch path.

## ROUTE 4 — OCDS registry (standard.open-contracting.org / data.open-contracting.org)

`https://data.open-contracting.org/en/publication/4` ("Canada:
Buyandsell.gc.ca | OCP Data Registry") — checked directly:

> Dataset description states **"This dataset is no longer updated by the
> publisher."** Coverage: **Apr 2013 – Nov 2015**, ~102,799 parties,
> 16,379 tenders, 31,134 awards, 50,107 contracts, last retrieved by the
> registry **2022-09-23**.

This is a dead, archived pilot from the predecessor system
(`buyandsell.gc.ca`, since replaced by CanadaBuys) — over a decade stale,
not updated in 4+ years even by the registry's own last-retrieval date,
and covers no security/cyber work from the live 2026 tender set. A
different, permitted host, but with no live data to fetch through it.

## OVERALL FINDING

| Route | Host permits us? | Has the live 966-row tender data? |
|---|---|---|
| open.canada.ca CKAN metadata | YES | NO — metadata only, `datastore_active=false`, points back to blocked host |
| Official CanadaBuys API | N/A — doesn't exist for this data | NO |
| OGL-Canada licence | N/A (governs reuse, not access) | N/A |
| OCDS registry (data.open-contracting.org) | YES | NO — dead 2013-2015 pilot |
| canadabuys.canada.ca direct (prior decision) | NO — blanket `Disallow: /` | YES, but blocked |

**No permitted route to the live CanadaBuys open-tender data exists.**
The one host that both permits us and carries current data
(`canadabuys.canada.ca`) is blocked by its own robots.txt with no
carve-out. The one host that mirrors the dataset and permits us
(`open.canada.ca`) carries only a pointer back to the blocked host, not
an independent copy. The one alternate-host registry that permits us
(`data.open-contracting.org`) has no live Canadian data. This is a
complete, evidenced negative finding, not an unresolved question.

## WHAT WOULD CHANGE THIS DECISION

- CanadaBuys updates `canadabuys.canada.ca/robots.txt` to allow
  `/opendata/` (or any path) for `User-agent: *`, matching what it
  already grants Bingbot/Googlebot by name.
- open.canada.ca's CKAN entry for this dataset gets `datastore_active:
  true` with the actual rows loaded into CKAN's own datastore (would
  make `datastore_search` against `open.canada.ca` a genuine independent
  copy, not a pointer).
- CanadaBuys publishes a documented API with an explicit access grant
  covering programmatic retrieval of live tender data on a host distinct
  from the blocked one.
- Canada resumes active OCDS publication with a live feed distinct from
  the dead 2013–2015 `buyandsell.gc.ca` pilot.

None of these is true today. No `foundation/mouth_canada.py` or test
file was built, per this task's own scope rule (file territory is
conditional on a permitted route existing).
