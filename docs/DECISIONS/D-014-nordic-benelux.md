# D-014 — Denmark, Netherlands cracked; Switzerland found and blocked

STATUS: TWO NEW MOUTHS BUILT AND TESTED (`foundation/mouth_udbud_dk.py`,
`foundation/mouth_tenderned_nl.py`). Switzerland's real API endpoint and
full parameter list were located but the endpoint itself sits behind an
anti-bot WAF that redirects any non-browser request — not built, not
bypassed.
DATE: 2026-09-03

## THE TASK

`GLOBAL_EUROPE.md` identified three national procurement portals as
promising and left every one of them unfetched past `robots.txt`:
Denmark's udbud.dk (fully permissive, purpose-built below-threshold
board), the Netherlands' TenderNed (`/aankondigingen/` not blocked),
Switzerland's simap.ch (confirmed English UI, GPA party, search URL not
located). This cycle fetched all three.

## DENMARK — udbud.dk: CRACKED

`udbud.dk/` is a client-rendered SPA. Its own JS bundle
(`/assets/js/main-*.js`, fetched and grepped, never executed) names the
real backend: `POST https://udbud.dk/soegning/public/soegeresultat`,
JSON body in, JSON out, no cookie, no session, confirmed live with a
bare `curl -X POST`. Full request body shape reverse-engineered from the
bundle's own Pinia store: `fritekstQuery` (free text),
`pagineringDto.{aktuelSide,maksElementer,sorteringFelt,retning}`,
`udbudStatusFilter` (`AKTIV`|`ALLE`), `filterDto.{...}`.

**Fabrication check, live 2026-09-03:**

| Query | `totaltAntalResultater` |
|---|---|
| `fritekstQuery="cyber"` | 5 |
| `fritekstQuery="zzzznonsensequery9999xyz"` | 0 |
| no `fritekstQuery`, `udbudStatusFilter="AKTIV"` | 2424 |

Three distinct outcomes for three distinct inputs — a genuinely honoured
filter, the first of three checked this cycle that passed on the first
parameter guess.

**Shape:** mixed stream of open competitions and past-award results
under one status filter — `formulartypeKode` (`"competition"` vs.
`"result"`) plus a non-empty `tidsfrister` (deadline) list is what
actually distinguishes an open opportunity; `udbudStatusFilter=AKTIV`
alone does not. `mouth_udbud_dk.py::parse_items()` enforces both.

**Language:** genuinely bilingual per notice (`dataDa`/`dataEn` parallel
blocks) — confirmed, not inferred.

**Value:** structured (`anslaaetVaerdi` + `anslaaetVaerdiValuta`), not
free text like Ireland's eTenders — still kept at `money_state=
NOT_OBSERVED`, this module has not audited the figure against the
underlying tender documents.

**robots.txt:** `Allow: /`, disallow list is nine logged-in-area paths;
`/soegning/` is not one of them.

### Live security/cyber notices found, 2026-09-03

| Title | Buyer | Value | Deadline | Notice | Language |
|---|---|---|---|---|---|
| Tender for a framework agreement on the delivery of Cybersecurity advisory and assessment services | Danmarks Nationalbank | 9,200,000 DKK | 2026-10-02T10:00:00Z | `https://udbud.dk/bekendtgoerelse/f104f4f6-8fc3-4624-b286-6968e40f18d1` | English (`dataEn`) |
| Managed Detection and Response (MDR) | Statens It | 24,000,000 DKK | 2026-09-17T12:00:00Z | `https://udbud.dk/bekendtgoerelse/0fd24aec-88bc-4201-94d6-f67011b01159` | English (`dataEn`) |

Foreign-supplier eligibility: not independently checked against a
udbud.dk source this cycle; Denmark is an EU member state (general
fact).

## NETHERLANDS — TenderNed: CRACKED, ELEVEN WRONG GUESSES FIRST

`/aankondigingen/overzicht` is an Angular SPA. Rather than reverse-
engineer its lazy-loaded chunks, the backend's own REST convention was
guessed directly and worked first try: `GET https://www.tenderned.nl/
papi/tenderned-rs-tns/v2/publicaties` — HTTP 200, unauthenticated,
Spring Data `Page<T>` JSON shape.

**Fabrication check, live 2026-09-03 — every one of these silently
ignored the value supplied, identical `totalElements: 145151` and
identical first record regardless:** `zoekterm`, `trefwoord`,
`zoekTerm`, `keyword`, `q`, `term`, `aanbestedingNaam`, `naam`,
`vrijeTekst`, `tekst`, plus the Dutch pagination names `pagina` and
`aantalPerPagina`. Same failure class this task brief named for
AusTender/GETS-NZ/World Bank/Singapore/Contracts Finder — eleven for
eleven.

**The real parameters are English, Spring Data's own convention:**
`page` and `size` (confirmed: `size=3` -> 3 records; `page=1&size=5`
returns a disjoint set from `page=0&size=5`; `size=200` -> HTTP 400,
`size=100` -> HTTP 200 — a real ceiling, not a silent clamp). The real
free-text filter is `search` (confirmed: `search=cybersecurity` ->
`totalElements: 176` with on-topic titles; `search=
zzzznonsensequery9999xyz` -> `totalElements: 0`).

**Shape:** full-text search across TenderNed's entire history
(a 2023 closing date and a `2034-06-25` outlier both appeared live in
one `search=cybersecurity` result set), no `open`/`status` parameter
found. `mouth_tenderned_nl.py::parse_items()` keeps only records whose
`sluitingsDatum` parses as a real future timestamp.

**Language:** Dutch only, confirmed — no parallel English field anywhere
in the response, resolving `GLOBAL_EUROPE.md`'s "not confirmed this
cycle."

**Value:** no estimated-value or currency field exists in this response
shape at all — worse than Ireland's free-text column, `money_state` is
always `NOT_OBSERVED` with no fallback text either.

**robots.txt:** redirects to `/cms/robots.txt`; disallows `/cms/search/`
specifically. `/papi/` is not under `/cms/` and is not named.

### Live security/cyber notices found, 2026-09-03 (future closing date only)

| Title | Buyer | Deadline | Notice | Language |
|---|---|---|---|---|
| SIEM, SOC, SOAR-dienstverlening | Veiligheidsregio Noord- en Oost- Gelderland | 2026-09-25T12:00:00 | `https://www.tenderned.nl/aankondigingen/overzicht/433831` | Dutch |
| Dienstverlening SIEM-SOC | Veiligheidsregio Haaglanden | 2026-09-28T12:00:00 | `https://www.tenderned.nl/aankondigingen/overzicht/435111` | Dutch |
| Informatiebeveiliging en cybersecurity (DPS/framework, unusually long deadline) | Radboud Universiteit | 2034-06-25T08:00:00 | `https://www.tenderned.nl/aankondigingen/overzicht/430417` | Dutch |
| Vervangen beveiligingsinstallaties PI Krimpen (physical security installations, borderline relevance) | Rijksvastgoedbedrijf | 2026-09-25T09:00:00 | `https://www.tenderned.nl/aankondigingen/overzicht/434225` | Dutch |

No value field present on any record (see above). Foreign-supplier
eligibility not independently checked; the Netherlands is an EU member
state (general fact).

## SWITZERLAND — simap.ch: API FOUND, BLOCKED BY AN ANTI-BOT WAF

`GLOBAL_EUROPE.md` left the search URL unlocated (`/en/publications`
404s). This cycle located it precisely: `/en` itself is the "Publications"
search page (a React app, `containers-ProjectManagerPage-Public` chunk).
Its main JS bundle (3.6MB, grepped, never executed) names the exact
endpoint and full parameter list: `GET /publications/v2/project/
project-search?search=&lang=&projectSubTypes=&issuedByOrganizations=&
processTypes=&newestPubTypes=&cpvCodes=&cpcCodes=&bkpCodes=&ebkphCodes=
&ebkptCodes=&npkCodes=&oagCodes=&orderAddressCountryOnlySwitzerland=&
orderAddressCantons=&newestPublicationFrom=&newestPublicationUntil=&
lastItem=` (cursor-paginated via `lastItem`, not page-numbered).

**Every live call to this endpoint — plain, with `Accept: application/
json`, with `X-Requested-With: XMLHttpRequest`, with a real session
cookie from a prior page load, with `Origin`/`Referer` headers matching
the real CORS response (`Access-Control-Allow-Origin: https://
www.simap.ch` genuinely reflected) — returned the identical result:
`HTTP 302 Found`, `Location: /en`, and a freshly minted `connect.sid` +
`SCDID_S` cookie pair on every single attempt, never the same session
twice.** The response header `Server: Secure Entry Server` and the
`SCDID_S` cookie shape are consistent with a bot-defense product issuing
a JS challenge before admitting a request — not a routing bug, not a
missing header this cycle failed to supply.

This is the same category of block already correctly declined for
AusTender in `tender_radar.py`'s own module docstring: a deliberately
installed control, not evaded by spoofing a browser. **Not built.** The
endpoint shape above is preserved here so a future cycle does not have
to re-derive it from the bundle if the block is ever independently
authorized to be worked around (e.g. a real browser automation tool, out
of this module's file territory and this task's rules either way).

## ROUTE TABLE

| Portal | robots.txt | Real endpoint | Method | Shape | Live filter proof | Language | Mouth |
|---|---|---|---|---|---|---|---|
| Denmark udbud.dk | `Allow: /`, 9-path logged-in disallow, `/soegning/` not in it | `https://udbud.dk/soegning/public/soegeresultat` | POST JSON body | Mixed open+award, `formulartypeKode`+`tidsfrister` distinguishes | `fritekstQuery`: 5 / 0 / 2424 for cyber / nonsense / none | Bilingual (`dataDa`/`dataEn`) | `foundation/mouth_udbud_dk.py` |
| Netherlands TenderNed | `/cms/search/` disallowed only; `/papi/` unblocked | `https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties` | GET query string | Full-history search, no open/status field — filtered client-side by closing date | `search`: 176 / 0 / 145151 for cyber / nonsense / none; `page`/`size` real, 11 other names decorative | Dutch only, no English field | `foundation/mouth_tenderned_nl.py` |
| Switzerland simap.ch | Publication paths not disallowed | `https://www.simap.ch/publications/v2/project/project-search` | GET, cursor-paginated (`lastItem`) | UNKNOWN — never reached past the WAF | N/A — every attempt 302'd before returning data | English UI confirmed on `/en` page shell; API response never seen | Not built — WAF-blocked |

## WHY THIS MATTERS FOR THE BELOW-THRESHOLD ARGUMENT

Both cracked sources return live, currently-open, English-or-native-
language notices TED does not carry — udbud.dk's cybersecurity advisory
tender (9.2M DKK) and TenderNed's two SIEM/SOC tenders are all national-
board-only opportunities, the exact hidden tier this task brief's Irish
five-document finding (EUR400k–2.6M turnover, EUR13M liability, three
references) makes the only realistically winnable lane for a solo
operator. Two more countries' below-threshold tiers are now open;
Switzerland's is found but gated, a genuine negative result rather than
an abandoned recon.

## NEXT STEPS (not executed this cycle)

1. Test udbud.dk's `udbudStatusFilter=ALLE` against `AKTIV` to confirm
   they actually differ, and exercise `pagineringDto.aktuelSide` beyond
   page 1 — both named CANNOT items in `mouth_udbud_dk.py`.
2. Confirm whether TenderNed's `search` parameter supports any
   open/status-narrowing companion parameter under a name this cycle
   didn't guess, rather than relying solely on the client-side
   closing-date filter.
3. If a real browser-automation tool is ever authorized for this
   project, the simap.ch endpoint and parameter list above are already
   fully specified and ready to use without further reverse-engineering.
