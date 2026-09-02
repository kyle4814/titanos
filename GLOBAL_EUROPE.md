# GLOBAL_EUROPE — Switzerland, Norway, Iceland/Liechtenstein, UK devolved
retry, Nordic EU national portals, Netherlands

STATUS: RECON ONLY. NO MODULE BUILT THIS CYCLE. DATE: 2026-09-03

## METHOD

Recon done with `WebFetch` (this session's own tool; identifies itself
however that tool's infrastructure does — not a hand-picked spoofed
browser or search-engine string set by this session). `robots.txt` was
read first for every target. Where `robots.txt` blocks a path, only
`robots.txt` itself was read, consistent with `docs/DECISIONS/D-010`
through `D-013`'s standing discipline. `WebSearch` was used for three
lookups (Iceland/Liechtenstein/Sweden portal identification) before
this session's search budget was exhausted (200/200) — those three
remain genuinely unresolved, marked UNKNOWN below, not guessed.

Several targets are JavaScript-rendered single-page applications;
`WebFetch` converts HTML to markdown and does not execute JS, so a
"reachable but thin content" result below means exactly that — the page
is not blocked, but this cycle's tooling could not see past the client-
side render to a search API. That is a recon limitation, not a finding
that no API exists.

## THE KEY INSIGHT, RE-APPLIED (per task brief)

`D-012`/`D-013` found that Ireland's `etenders.gov.ie` e-PPS deployment
has a decoy: `prepareCurrentOpportunities.do?currentType=cft` always
302-redirects to `quickSearchAction.do?searchType=cftFTS&latest=true`,
and **that redirect target**, fetched directly with the right query
string, is the real, stateless, keyless results page with genuine
pagination (`d-3680175-p=N`). D-010/D-012 had only tested the *prepare*
page for NI and Malta and found a bare form; this cycle went straight to
the *redirect target* URL for both, exactly as the task brief asked.

**Result: the insight does NOT transfer to NI or Malta at this
endpoint.** Both are confirmed live, same platform vendor family
(European Dynamics, matching `<title>` branding), but requesting the
identical URL shape that unlocks Ireland's data
(`quickSearchAction.do?searchType=cftFTS&latest=true`) returns an
**"Advanced search" form page**, not embedded results, on both sites —
not the shape D-012 already ruled out (a bare "Simple search" landing
page) but a *different* bare form, still with zero `resourceId` matches
and no "results in total" marker. Malta's version additionally surfaced
a CAPTCHA-mismatch message on the same fetch, which Ireland's endpoint
never has. This is a genuine, deeper negative result than D-012's: it is
not "we didn't reach far enough," it is "the same URL shape that works
for Ireland does not work for NI or Malta" — each e-PPS deployment is
independently configured, confirming D-012's own tentative conclusion
rather than reversing it. **NOT BUILT. NI and Malta remain unresolved —
the next real test, not attempted this cycle, is finding each site's own
equivalent redirect chain rather than assuming Ireland's query string
transfers.**

Sell2Wales was also re-checked against this insight and found not to
apply for a structural reason the task brief's framing didn't anticipate:
**Sell2Wales does not run the e-PPS platform at all.** Its search page is
`/Search/Search_MainPage.aspx` (ASP.NET, not the Java/Struts `.do`
pattern of e-PPS) — confirmed again this cycle (D-010's original
finding stands). The page is reachable and shows "3345 Results" with
pagination controls (1–335), but result loading is client-side
JavaScript with no visible `<form>` action or `/api/` path in the
fetched markup — genuinely a different unresolved problem (JS-rendered
search) than NI/Malta's (wrong-shaped e-PPS response), not something
the redirect insight could have fixed either way.

## ROUTE TABLE — PRIORITISED

| Priority | Route | robots.txt verdict | Reachable | Language | Shape | Foreign eligibility | Live cyber work |
|---|---|---|---|---|---|---|---|
| 1 | Denmark — udbud.dk (below-threshold national board) | 200 OK, permissive — only blocks logged-in areas (`/ordregiver/`, `/opretIndkoeb/`, `/agent/`, `/konfig/`, `/indstillinger/`), explicitly `Allow: /` | YES, not deep-tested | Danish (UI); not checked for English notices | UNKNOWN — listing page not fetched this cycle | UNKNOWN | UNKNOWN |
| 2 | Netherlands — TenderNed | 200 OK, permissive except `/cms/admin/`, `/cms/user/login`, `/cms/user/register/`, **`/cms/search/`** (the CMS's own internal search engine is disallowed; the public notice-listing path `/aankondigingen/...` is NOT under `/cms/` and is not disallowed) | YES (`/aankondigingen/overzicht` returns 200) | Dutch UI confirmed (title "Aankondigingen" = "Announcements"); English toggle not confirmed this cycle | JS-rendered — listing content not visible via this tool; no query-string search pattern captured | UNKNOWN — high English proficiency in NL is a general fact, not a checked eligibility rule | UNKNOWN |
| 3 | Switzerland — simap.ch | 200 OK; blanket `Disallow` on admin/user/vendor/template/error/draft paths per language prefix (`/de/admin`, `/fr/admin`, `/it/admin`, `/en/admin`, etc.), sitemap declared (`/assets/sitemap.xml`) — publication/search paths NOT in the disallow list found | YES — `/en` loads with genuine English UI ("Search for publications", "Public procurement", "Vendor directory") | **English confirmed available** alongside DE/FR/IT — a real, positive finding | Publication search page path not yet located (`/en/publications` 404s — wrong guess, not a block) | Switzerland is a WTO GPA party (same status as Australia) — reciprocal covered-procurement access plausible above GPA thresholds; not independently verified this cycle, and cantonal below-threshold rules are a genuine unknown | UNKNOWN |
| 4 | Norway — Doffin.no | 200 OK, fully permissive (`User-agent: * / Disallow:`) | YES | Norwegian UI observed; `/en/` path exists but rendered content still showed the Norwegian title — inconclusive on whether English notices exist, JS-rendering likely hid the real content | JS-rendered SPA — no API/search endpoint located this cycle | Norway is EEA + WTO GPA party; Doffin explicitly exists to carry Norway's own below-threshold notices alongside TED-linked above-threshold ones (well-established public fact about Doffin's role, not independently re-verified against its own about-page this cycle) | UNKNOWN |
| 5 | Finland — Hilma (hankintailmoitukset.fi) | No robots.txt published (404) — same "not blocked" reading D-010/D-012 gave NI/Ireland/Malta's 302 | YES — `/en/` loads | English page exists (confirmed reachable) but returned only minimal content ("Hilma" + short descriptor) — JS-rendering limitation, not a block | JS-rendered — search shape not located this cycle | UNKNOWN | UNKNOWN |
| 6 | Sweden — TendSign/Kommers (Opic) | UNKNOWN — `tendsign.se` failed TLS certificate validation against this tool (cert registered to `opic.com`/`*.opic.com`, meaning the real current domain is under Opic's own domain, not `tendsign.se`); `utbudsplattsen.se` did not resolve (DNS failure) | NOT RESOLVED — correct current domain not identified this cycle (WebSearch budget exhausted before this could be looked up) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| 7 | Mercell (multi-country aggregator incl. Norway/Nordics) | 200 OK, permissive except nine specific customer-campaign landing pages (`/*/*/<id>/innskuddspensjon-for-akasia-*`) — not a blanket disallow | YES | Multi-language platform (per URL slugs seen: `-tender`, `-anbud`, `-udbud` variants) | Not tested this cycle beyond robots.txt | UNKNOWN | UNKNOWN |
| — | UK — Sell2Wales | Empty robots.txt (fully permitted) — unchanged from D-010 | YES — search page loads, shows "3345 Results" | English (Wales's other official language is Welsh; UI observed in English) | Client-side JS — no `<form>` action or `/api/` path found in fetched markup. **Confirmed: NOT the e-PPS platform** — ASP.NET (`Search_MainPage.aspx`), not the `.do`-pattern Java/Struts platform NI/Ireland/Malta share, so the redirect insight structurally does not apply here | UNKNOWN | UNKNOWN |
| — | UK — eSourcing NI | No robots.txt published (302 redirect to homepage) — unchanged from D-010/D-012 | YES — e-PPS platform confirmed | English | **Redirect insight applied, did not transfer** — `quickSearchAction.do?searchType=cftFTS&latest=true` (Ireland's working URL) returns an "Advanced search" **form** page here, not embedded results | UNKNOWN | UNKNOWN |
| — | Malta — eTenders | No robots.txt published (302 redirect to homepage) — unchanged from D-010/D-012 | YES — e-PPS platform confirmed | English (Malta's official language alongside Maltese) | **Redirect insight applied, did not transfer** — same URL returns an "Advanced search" form page, additionally surfacing a CAPTCHA-mismatch message not present on Ireland's endpoint | Malta is an EU member state; English is an official language (already noted in D-010) | UNKNOWN |
| — | Iceland | UNKNOWN | `utbod.is` returned 404; correct domain not identified this cycle | UNKNOWN | UNKNOWN | Iceland is EEA (not independently re-verified against a source this cycle) | UNKNOWN |
| — | Liechtenstein | UNKNOWN | `simap.li` did not resolve (DNS failure); correct domain not identified this cycle | UNKNOWN | UNKNOWN | Liechtenstein is EEA (not independently re-verified against a source this cycle) | UNKNOWN |

## WHAT THIS CYCLE ACTUALLY ESTABLISHES

- **Denmark's udbud.dk is the strongest new lead**: fully permissive
  `robots.txt`, purpose-built as the below-threshold national board
  (the exact tier this task brief prioritises), not previously checked
  in D-010/D-012/D-013. Not yet fetched past `robots.txt` — the next
  concrete step, not a dead end.
- **Switzerland's English-language UI is a real, positive, confirmed
  finding** — genuinely different from every EU-adjacent e-PPS site
  checked so far, which have all been single-language or JS-opaque.
  The actual publication-search URL remains unlocated.
- **The e-PPS redirect insight, tested rigorously against NI and Malta
  this cycle, does not transfer.** This is a genuine negative result,
  not an abandoned recon — each e-PPS deployment needs its own redirect
  chain traced from scratch, the same way D-012/D-013 traced Ireland's.
- **TenderNed's `robots.txt` disallows its own internal search engine
  path (`/cms/search/`) specifically**, while leaving the public notice-
  listing path unblocked — a distinction worth remembering if a future
  cycle builds against this site: crawling `/cms/search/` directly would
  violate a real declared rule; using `/aankondigingen/...` would not.
- **Sweden's procurement-platform domain migrated away from
  `tendsign.se`** (now serving a mismatched TLS cert pointing at
  `opic.com`) — a real infrastructure fact, not a dead end, but the
  correct current domain needs a lookup this cycle's exhausted search
  budget could not perform.
- **Iceland and Liechtenstein remain genuinely unresolved** — no
  fabricated domain guess is recorded as a finding; both need a fresh
  lookup in a future cycle.

## NEXT STEPS (not executed this cycle)

1. Fetch `udbud.dk`'s actual notice-listing page and look for a
   query-string-driven search — the single most promising unopened lead
   from this cycle, on the exact below-threshold tier this task
   prioritises.
2. Locate simap.ch's real publication-search URL (the guessed
   `/en/publications` 404s; the homepage's own "Search for publications"
   link was not followed this cycle).
3. Resolve Sweden's correct current procurement-portal domain and
   Iceland/Liechtenstein's correct portal domains via a fresh
   `WebSearch` budget.
4. Trace NI's and Malta's own redirect chains from their respective
   `prepareCurrentOpportunities.do` pages independently, rather than
   assuming Ireland's downstream URL shape — the task this cycle
   completed was testing the *transfer* hypothesis (now falsified), not
   independently solving NI/Malta from scratch.

None of the UNKNOWN rows above is a proven dead end; each has a named,
concrete next action.
