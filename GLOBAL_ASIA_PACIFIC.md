# Global Expansion — Asia-Pacific Procurement Route Table

STATUS: RESEARCH COMPLETE — NO MODULE BUILT THIS CYCLE.
DATE: 2026-08-19
OPERATOR PROFILE: solo, Australia, ABN, no certifications, no insurance,
no corporate references, English only, remote-capable.

READ FIRST: `docs/DECISIONS/D-007-new-sources.md` — Singapore GeBIZ
already rejected (award-only data; foreign suppliers need a
Singapore-incorporated entity). Not redone here — no different route
was found.

## METHOD

Live checks only, from this machine: `curl` for robots.txt (quoted
verbatim where found) and reachability, `WebFetch`/`WebSearch` for
content. **No User-Agent spoofing anywhere in this cycle** — a block
(robots.txt disallow, 403, Cloudflare challenge, TLS reset) is recorded
as a finding, not routed around. No source, rule, or notice is
asserted without the fetch that produced it; anything not directly
verified is marked **UNKNOWN**. Four parallel research passes fed this
table: Japan+Korea, India+HK+Taiwan, SE Asia (5 countries), and
Pacific islands + donor-funded procurement.

---

## RANKED ROUTE TABLE

Ranked by: reachable (no spoof) → English → open shape → foreign
eligibility confirmed or plausible → live IT/cyber content. A market
failing English, reachability, or (for GPA-relevant markets) GPA
membership was not pursued to full depth.

| Rank | Source | Robots | Reachable | English | Shape | Foreign eligibility | Live cyber/IT | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **AusConnect** (`ausconnect.dfat.gov.au`) — DFAT's aid sub-contracting portal | Standard Drupal disallow list only; one addition `Disallow: /run/opportunities` (the JSON endpoint, not the page) | 200 OK, `/opportunities` reachable | Yes, full | **Live and populated** — real current sub-contract notices from DFAT's managing contractors (Tetra Tech, DT Global, Abt Global, Cowater, Chemonics, Palladium) | Per-notice, set by the managing contractor (not a blanket DFAT rule) — e.g. one Vanuatu role requires "right to work in Vanuatu... or eligibility for a Development Support Visa"; others are open to Australia-based applicants by construction (AU managing contractors sub-contracting AU/local specialists) | **None found at check time** — scanned live listing for "cyber"/"ICT"/"information technology": 0 hits | **Standing watch target.** The one channel confirmed open, unblocked, live, and structurally reachable for a solo AU contractor. Bypasses AusTender's WAF block entirely by being a different portal. Revisit regularly — content turns over. |
| 2 | **ADB** business/eligibility pages (`adb.org`) | robots.txt permits `/projects/tenders` itself, disallows only export formats (`csv`/`rss`) | Static/policy pages 200 OK. **Live tender endpoint `/projects/tenders` = repeatable Cloudflare 403** (confirmed, not routed around) | Yes, default | Cannot confirm — notice list is the blocked endpoint | **Confirmed and quoted**: *"contractors bidding for contracts fully or partially financed or administered by ADB should have the nationality of an ADB member country, unless the financing agreement specifies otherwise."* Australia is a founding ADB member — qualifies by default, per-project financing agreement governs specifics. Source: `adb.org/business/how-to/what-are-main-eligibility-requirements-bidding-contracts-under-adb-financed-projects` | **UNKNOWN** — not "none found," genuinely unreachable to check | Best-in-class *rule*, worst-in-class *access*. The donor-overrides-recipient hypothesis is proven true here on paper; the live-notice feed itself is Cloudflare-gated to non-browser clients. Not buildable as a scraper without violating the no-spoof rule. |
| 3 | **PNG — National Procurement Commission** (`npc.gov.pg`) | Standard WordPress/WooCommerce disallow list, no bot block | 200 OK | Yes | "Tender Advertisements" section, live | UNKNOWN — page references an eligibility-requirements PDF, not extracted this cycle | **YES — confirmed live**: RFP NPC/2026/26 for an "electronic Government Procurement (e-GP) System," explicitly scoped to include "cybersecurity risk assessment and testing." The only genuinely live cyber-adjacent notice found anywhere in this entire research cycle. | Real, current, reachable. Eligibility PDF is the one document worth pulling next — everything else about this listing is good. |
| 4 | **Philippines — PhilGEPS** (`notices.philgeps.gov.ph`) | No robots.txt (404 — unrestricted) | 200 OK, no challenge | Yes, full English UI | "OPPORTUNITIES" nav confirmed to exist; live listing/closing dates not pulled this cycle | UNKNOWN — GPPB Resolution 15-2021 referenced on-site but not read verbatim; Philippines is GPA **observer only**, not a party | UNKNOWN — not checked | Reachable, unblocked, English — strongest SE Asia candidate on access grounds. Next step: pull GPPB Resolution 15-2021 text and a live opportunities listing before any build decision. |
| 5 | **Vietnam — muasamcong.mpi.gov.vn** | `Disallow:` — fully open | 200 OK (slow, ~5.7s, not challenged) | Confirmed EN/VI toggle | Tender-search function exists; open-listing dates not pulled this cycle | Promising signal, not yet a quoted rule: site surfaces a dedicated "foreign contractor/investor" registration flow and a public list of "foreign contractors who have won bids in Vietnam." Vietnam is GPA **observer only**. Underlying Bidding Law/Decree text not yet pulled. | UNKNOWN | Second-strongest SE Asia candidate. The foreign-contractor pathway being *visible on the surface* (unlike Malaysia/Thailand/Indonesia) is the standout finding — needs the Decree text quoted before building. |
| 6 | **Japan — JETRO Government Procurement Database** (`jetro.go.jp/en/database/procurement/`) | Only `WiSEWebCrawler` restricted; generic client unrestricted | 200 OK | Yes, full English | Real search tool (date range, entity, category incl. "0071 Computer & Related Services") covering GPA/EPA/CEPA-scope notices — **but form/session-driven, not a static feed**; WebFetch could not execute the search itself | Not directly quoted this cycle — GPA Article IV national-treatment obligation applies to GPA-covered procurement by treaty design (general knowledge), but JETRO-specific eligibility sentence not found in fetched text. Japan **is** a GPA party. | UNKNOWN — category filter exists, no notice retrieved | Cautiously worth building — but requires a POST/session-aware fetch, not a simple GET scrape. Second-cycle work if pursued. |
| 7 | **Taiwan — web.pcc.gov.tw** | robots.txt request 302s to the live homepage — no enforced disallow | 200 OK (via `/pis/` path) | zh-tw default; English portal depth **not confirmed live** this cycle (WebSearch quota exhausted mid-check) | Not verified this cycle | Taiwan **is** a GPA party (mutual membership with Australia) — general knowledge, not re-verified against the WTO page this cycle | UNKNOWN | Most legally favourable of the GPA markets on paper (mutual GPA membership), technically reachable — but needs a dedicated follow-up pass to confirm English depth and pull a live listing before ranking above Japan. |
| 8 | **Malaysia — ePerolehan** (`eperolehan.gov.my`) | `Disallow:` — fully open | 200 OK | Confirmed bilingual (EN/BM toggle) | "Notis Sebut Harga/Tender" section exists; open-listing visibility without login not confirmed | UNKNOWN — no Bumiputera/eligibility text found on homepage. Malaysia is GPA **observer only** (since 2012, confirmed live against WTO's page). | UNKNOWN | Reachable and bilingual — worth a second pass into the tender-search page itself, but not prioritised over PH/VN given weaker surface signal on foreign access. |
| 9 | **Fiji — Fiji Procurement Office** (`fpo.gov.fj`) | Standard Joomla disallow (admin/cache), no bot block | 200 OK | Yes | Homepage links an "eTender Portal" and "Future Opportunities" — not confirmed one hop deeper | UNKNOWN | Not confirmed present or absent | Reachable, unblocked, English — worth a follow-up hop into the eTender subdomain; no live cyber content confirmed yet. |
| 10 | **Samoa — Ministry of Finance** (`mof.gov.ws`) | Minimal (sitemap directive only) | 200 OK (Cloudflare-fronted Webflow) | Yes | "TENDER ADVERTISEMENTS" section, live postings confirmed (medical consumables, engineering roles, airport infra) | UNKNOWN | **None currently visible** | Reachable, genuinely live tender board — but nothing IT/cyber-shaped at check time. |
| 11 | **India — CPPP/eProcure** (`eprocure.gov.in`) | No robots.txt (404 — unrestricted) | 200 OK | Yes | **Confirmed open** — active tenders with Sep–Oct 2026 closing dates, plus corrigendums; not awards-only | UNKNOWN at portal level — eProcure is an aggregator, eligibility set per-tender by the procuring entity; India is **not** a GPA party, and general Indian policy (Make in India / GFR Rule 144-XI "restricted global tender") can bar or disadvantage foreign bidders tender-by-tender. No blanket rule to quote. | Not confirmed in this pass | Reachable, English, genuinely open shape — but eligibility is fragmented per-listing with a non-GPA policy backdrop that skews against foreign solo bidders. Needs tender-by-tender screening, not a blanket source build. |
| — | **South Korea — PPS/KONEPS** | `pps.go.kr`: only Googlebot restricted. `koneps.go.kr`: robots.txt unreadable (see reachability) | `pps.go.kr` reachable. **`koneps.go.kr` (the actual transactional system) fails at TLS handshake** — `SSL_ERROR_SYSCALL`, connection reset before any HTTP response; reported as a block, not bypassed | PPS English site (`pps.go.kr/eng/`) is informational-only; no live English bid database located; KONEPS itself understood to be Korean-language-dominant (not independently confirmable — site unreachable) | UNKNOWN | UNKNOWN — Korea is a GPA party, but no Korea-specific eligibility text was verified live | UNKNOWN | **Not viable now.** The system that matters is TLS-blocked to a plain client; the reachable English site is a brochure page. Revisit only if the block lifts or a legitimate browser-based path becomes available. |
| — | **Hong Kong** | `gld.gov.hk/robots.txt` → custom 404 (no file) | `gld.gov.hk` root/`/en/` = 200 but pure JS-shell, no static content reachable without JS execution; `www.gets.gov.hk` failed on **TLS certificate hostname mismatch** (broken cert, not a block — did not proceed past it); actual e-Tendering System URL **not located** this cycle | Presumed yes (bilingual by law) — not confirmed against live content | UNKNOWN | Hong Kong, China **is** a separate WTO GPA party (confirmed live against WTO's page: GPA 1994 in force 1997, GPA 2012 in force 2014) — legally the most favourable status of any market in this table | UNKNOWN | Legally promising, operationally unverified. The portal itself was never actually reached — needs a dedicated re-check with the correct current GLD e-Tendering URL, not a judgement on the market. |
| — | **Thailand — e-GP** (`gprocurement.go.th`) | **`Disallow: /` for `User-agent: *`, on both hostnames checked** — explicit, blanket | Technically 200 on root, but a JS-redirect shell in `windows-874` (Thai codepage); real paths 404 | No evidence of English; codepage is a strong native-language-only signal | UNKNOWN | UNKNOWN | UNKNOWN | **Excluded.** robots.txt explicitly disallows all automated access — this is respected, not routed around, per the same standard applied to CanadaBuys in D-007. |
| — | **Indonesia — LPSE/INAPROC** | `inaproc.id`: Cloudflare-style **403** on robots.txt itself. `lpse.go.id`: **does not resolve** (stale/wrong domain) | `inaproc.id` 403 direct and via WebFetch (respected, not bypassed); `lkpp.go.id` (policy agency) 200 but content fetch failed twice (socket hang-up) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | **Not viable as researched.** Both given portal names are wrong/blocked. Would need fresh URL discovery for the current SPSE endpoint before any further judgement — not a "no" on Indonesia as a market, just on these two URLs. |
| — | **India — GeM** (`gem.gov.in`) | UNKNOWN — server unreachable | **Connection timeout**, twice, across curl and WebFetch, no UA spoofing — network-level block or geo/IP filtering, not transient | UNKNOWN | UNKNOWN | UNKNOWN — general knowledge (not verified live) suggests GeM applies "Preference to Make in India" domestic-preference rules and has historically required Indian entity credentials (PAN/GST/Indian bank account) to register at all, which would functionally exclude a foreign sole trader — but this could not be confirmed against the live site | UNKNOWN | Unreachable from this environment. Even if reachable, general knowledge points toward a foreign-entity registration barrier — flag for a manual check from a different network before investing further. |
| — | **World Bank — Procurement Notices UI** (`projects.worldbank.org`, `search.worldbank.org/api/v2/procnotices`) | `Allow:*`, only technical paths disallowed | 200 OK, no auth | Yes | **Confirmed broken, again, with new detail**: the country-filterable UI (`project_ctry_name_exact=`) works correctly (verified per-country totals differ), but sorting by most-recent `submission_date` across 12 Pacific countries returned **zero** notices with a future deadline at check time, and `notice_status` never distinguishes open from closed (always "Published"). Extends, does not contradict, the D-007 finding. | Plausible in principle (member-country framework) — moot, shape fails first | **Zero** cybersecurity/IT-services consulting notices found across 12 Pacific countries sampled; only closed-award ICT *goods* (printers, laptops) in 3 countries | **CANNOT** — same shape flaw as D-007, now confirmed at the country-filtered UI layer too, not just the bulk API. |

---

## KEY FINDINGS, COMPRESSED

**FINDING → IMPLICATION → DECISION**

1. **AusConnect exists, is open, and is structurally the right shape** →
   it is DFAT's actual aid-delivery procurement channel (managing
   contractors sub-contract through it), not a decoy →
   **watch it on a recurring basis; no cyber/IT work today, but it is
   the one confirmed-live, confirmed-open, English channel in the
   entire donor tier.**

2. **ADB's eligibility rule is the clearest "donor overrides recipient"
   proof found this cycle** (quoted: nationality of any ADB member
   country qualifies, Australia is a founding member) →
   but the live notice feed is Cloudflare-blocked to non-browser
   access → **the rule is proven, the pipe is not; do not build a
   scraper against a 403.**

3. **PNG's NPC has the only genuinely live cyber-adjacent notice found
   in this entire research pass**, across four parallel agents
   covering 15+ markets → small, English-speaking, Australia-adjacent
   markets with a functioning WordPress-based tenders page beat larger
   "sophisticated" portals on raw reachability → **pull PNG's
   eligibility PDF next; this is the nearest actionable lead.**

4. **India, Malaysia, Philippines, Thailand, Indonesia, Vietnam are all
   non-GPA** (Philippines/Thailand/Indonesia/Vietnam/Malaysia hold GPA
   Committee **observer** status only, confirmed live against WTO's
   page; India is not even an observer on procurement) → GPA
   membership cannot be assumed as a foreign-access guarantee anywhere
   in SE Asia → **eligibility must be established per-market from
   actual statute text, not inferred from portal reachability. None of
   the SE Asia eligibility rules were fully quoted this cycle — that
   is the single biggest gap left for a follow-up pass.**

5. **Thailand's robots.txt is a blanket `Disallow: /`** — the same
   deliberate-publisher-choice class of block D-007 already documented
   for CanadaBuys and AusTender → **excluded, not evaded, consistent
   with prior doctrine.**

6. **Korea's actual transactional system (KONEPS) is TLS-blocked to a
   plain client**; only the brochure-tier PPS English page is
   reachable → **not viable now; distinct from a robots.txt block, so
   worth a periodic recheck rather than a permanent write-off.**

7. **Hong Kong has the single best legal status in this whole table**
   (its own separate, confirmed GPA party status) but its actual
   tendering portal was never located this cycle — a pure research
   gap, not a market judgement → **highest-value follow-up target for
   a dedicated next pass: find the current GLD e-Tendering System URL.**

8. **The World Bank's procurement data — bulk API (D-007) and now the
   country-filtered UI (this cycle) — is consistently unusable for
   finding currently-open notices**, and carries zero live Pacific
   IT/cyber consulting work in the sample checked → **write this off
   as a source, not just for this cycle but structurally; the shape
   defect is now confirmed at two different access layers.**

---

## WHAT WAS NOT BUILT THIS CYCLE, AND WHY

Per the repository's Next-Lever Sequencer, a lower rung (build a
scraper/mouth module) is not legitimate while a higher rung (verify
eligibility, confirm reachability, quote the actual rule) is still
open. None of the fifteen-plus markets checked here passed all of:
reachable-without-spoofing + English + open-shape +
foreign-eligibility-quoted + live-cyber-content-confirmed,
simultaneously. AusConnect and PNG's NPC come closest on access; ADB
comes closest on the eligibility-rule axis; none clear the bar on all
five at once. No `.py` file was written. Nothing was registered,
submitted, or contacted.

## NEXT MOVE

Pull PNG NPC's linked eligibility PDF (`npc.gov.pg`, RFP
NPC/2026/26) and re-check AusConnect's `/opportunities` listing on a
recurring cadence (weekly) — these are the two closest-to-actionable
leads, and both are already fully reachable with no further access
research needed. Everything else in this table (HK's real portal URL,
Taiwan's English depth, SE Asia eligibility statute text, Japan's
session-driven search) is a second-cycle research task, not a build
task.
