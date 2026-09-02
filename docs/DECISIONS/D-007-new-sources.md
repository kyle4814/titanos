# D-007 — New procurement sources beyond TED/UK/NZ: one excellent
# near-miss, zero sources pass all five criteria. No mouth built.

STATUS: DECISION RECORDED — NO MODULE BUILT.
DATE: 2026-09-02

## THE QUESTION

TED (EU), UK Contracts Finder, and NZ GETS are already built and
exhausted (`mouth_ted.py`, `tender_radar.py`, `mouth_gets_nz.py`).
Australia is WAF-blocked (D-003, D-006). This cycle's job: find NEW
reachable sources carrying security/pentest work genuinely open to a
solo, Australia-based operator with no certifications, no insurance, no
corporate references, no staff, English only — real, machine-readable
feeds (RSS/Atom/OCDS/JSON), no auth or free registration only, verified
live, never by spoofing a User-Agent to defeat a WAF or robots.txt.

## HOW EVERY SOURCE WAS TESTED

`curl` and live fetches from this machine, with an honest identity (no
`bingbot`/`Googlebot`/spoofed UA anywhere in this cycle) — robots.txt
read and quoted verbatim, HTTP reachability checked, and where a feed
existed, its actual bytes downloaded and inspected in Python for shape
(does any record carry a genuine open/future closing date, or is
100% of it already-decided award data — the exact defect that killed
the AusTender OCDS mirror in D-006: 50,269 records, 0 with
`tender.tenderPeriod`) and content (security/pentest/cyber keywords in
titles/descriptions). No claim below is asserted without the fetch that
produced it.

## ROUTE TABLE

| Source | robots.txt | HTTP | Shape | Foreign-eligible | Security work now | Verdict |
|---|---|---|---|---|---|---|
| **CanadaBuys** (`canadabuys.canada.ca`) | `User-agent: bingbot`/`Googlebot` → permissive; `User-agent: *` → **`Disallow: /`** (blanket) | 200, CSV downloads OK for a generic UA | **EXCELLENT** — 966 rows, `tenderStatus`=`Open` for all, `tenderClosingDate` field, 867/966 close in the future | Plausible via CPTPP/WTO GPA (Canada-Australia both members) — not independently verified this cycle | **YES, live** — "Cyber Threat Intelligence Platform" (closes 2026-09-08), "Security Services" (2026-09-15), "IDEaS Program" security R&D (2027-03-31), 14 security-titled open notices total | **BLOCKED BY ROBOTS.TXT.** Everything else about this source is the best result of the cycle — see below. |
| Ireland eTenders (`etenders.gov.ie`) | `/robots.txt` 302→homepage (no file exists → no restriction) | 200 | No live open-tender feed found anywhere (checked the site itself and the third-party `publicprocurement.ie` WordPress aggregator, which only re-publishes the site's own web pages, not a real feed). The only machine-readable artifact is the OCP Data Registry's 6-monthly bulk snapshot (153,777 tenders + 43,223 awards mixed, last retrieved 2026-06-27, licensed **CC BY-NC-SA 4.0 — non-commercial**), which is a stale historical archive, not a live open-opportunities feed | n/a — moot | n/a — moot | **CANNOT** — no machine-readable open-opportunity feed exists |
| SAM.gov (US federal, `sam.gov`/`api.sam.gov`) | permissive (standard Drupal robots, no blanket disallow) | Get Opportunities Public API exists (`api.sam.gov/opportunities/v2/...`) | Real, keyed JSON API (not tested further once the eligibility gate below was found) | Legally foreign entities CAN bid on many US federal contracts, but the *practical* gate is severe for this operator: an API key requires a SAM.gov account, which requires entity registration (a Unique Entity ID, and for a non-US entity an NCAGE code obtained through a separate national codification bureau) — this is "free registration" in name but is a multi-step identity-verification process this operator's profile (no corporate registration, solo) is not built for. Separately, US federal cybersecurity/pentest work routinely carries citizenship/US-person or clearance requirements | not reached | **CANNOT (practical barrier)** — registration overhead disqualifies a solo foreign operator before any feed question matters |
| UN Global Marketplace (`ungm.org`) | selective disallow (specific paths only, not blanket) | 200, tender-notice browsing works in a normal web UI | No public API or RSS found anywhere — searched vendor guides, UNGM's own help docs, and the site itself; every reference found is to the web portal, gated behind tiered registration to see full opportunity detail | n/a — moot | n/a — moot | **CANNOT** — no machine-readable feed exists without registration |
| World Bank procurement notices (`search.worldbank.org/api/procnotices`) | no robots.txt (404 → unrestricted) | 200, real live JSON API, **no auth**, 417,243 total records | **WRONG SHAPE, functionally.** A `submission_date`/deadline field genuinely exists, but the API's own `strdate`/`enddate`/`sortfield`/`sortorder`/`notice_status_exact` parameters are silently accepted and ignored — total record count and record order did not change under any of them (the same "unrecognised parameter accepted and does nothing" failure class `tender_radar.py` already names for Contracts Finder's CPV param). Scanned 12,000 live `Invitation for Bids` records client-side: **zero** had a future `submission_date`. No `notice_status` value corresponding to "still open" exists in the data (`Draft`/`Revised`/`Cancelled` only) | Yes in principle — World Bank procurement rules favor international competitive bidding across member countries | **Confirmed historically** — "Cyber Security Incubator", "Set up a Cybersecurity CERT for the Health Care Sector", "National Security Operation Centre" all appear as real past notices | **CANNOT** — reachable and unauthenticated, but no mechanism (server- or client-side, at reasonable scan cost) reliably isolates currently-open notices |
| ADB / EBRD / EIB | not fully characterised — EBRD explicitly requires ECEPP portal registration for its own procurement notices | HTML-only business-opportunities pages found for all three | No machine-readable feed found for any of the three | n/a | n/a | **CANNOT** — no feed found; EBRD additionally gated behind registration |
| NATO NSPA (`nspa.nato.int`) | **could not even read robots.txt** — Cloudflare bot-challenge page (`cf-mitigated`, "Just a moment...") returned instead, HTTP 403 | 403 | n/a | n/a | n/a | **BLOCKED** — same WAF class as AusTender; not evaded |
| Singapore GeBIZ / `data.gov.sg` "Government Procurement via GeBIZ" | fully permissive (`User-agent: * / Allow: /`) | 200, real open `datastore_search` API, **no auth** | **WRONG SHAPE** — every field is award-shaped (`award_date`, `tender_detail_status` = `"Awarded to Suppliers"`, `supplier_name`, `awarded_amt`); confirmed live on real records, not assumed | **NO** — foreign companies cannot register as a GeBIZ Trading Partner (required to bid) without a Singapore-incorporated entity or local partner; Singapore's WTO-GPA membership guarantees access in principle, registration mechanics deny it in practice for a solo foreign operator with no local entity | n/a — moot, data is award-only | **CANNOT** — disqualified on two independent grounds (shape and eligibility) |
| Inter-American Development Bank (`data.iadb.org`) — found opportunistically while researching MDBs, not on the original candidate list | disallows `/api/`, `/dataset/download/`, `/file/download/` (singular) explicitly; the actual CSV lives at `/files/download/...` (plural) which the stated rules do not literally match, but the same section's own comment ("Block direct download paths to force landing page traffic") plainly intends to cover it — treated as effectively disallowed rather than exploiting the wording gap | 200, real CC BY 4.0 CSV, no auth | **WRONG SHAPE** — bulk historical archive (years 2000–2025), a real `deadline` column exists but only 1 row out of the full file had a future date (a long-horizon General Procurement Notice, not a hard bid deadline) | Australia is not an IDB member country (not independently re-verified this cycle — flagged as a probable but unconfirmed disqualifier) | Confirmed historically — 79 security/cyber-titled notices found (e.g. "Cybersecurity Infrastructure Strategy Development") | **CANNOT** — wrong shape, and the robots posture leans disallow even where the literal path string doesn't match |

## THE HEADLINE FINDING: CANADABUYS

Every dimension except robots.txt was excellent, verified live:

- `https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv`
  — 966 rows, every one `tenderStatus-appelOffresStatut-eng = "Open"`,
  867 with a `tenderClosingDate` still in the future relative to
  2026-09-02.
- Real, current, unambiguous security/pentest-adjacent work sitting in
  that file right now: *"Cyber Threat Intelligence Platform"* (closes
  2026-09-08), *"Security Services"* (2026-09-15), *"Third Party
  Security Services (Retender)"* (2026-09-10), *"IDEaS Program –
  Competitive Projects"* defence-security R&D (closes 2027-03-31).
- License: Open Government Licence – Canada (permissive, unlike
  Ireland's CC BY-NC-SA find above).
- A `tradeAgreements-accordsCommerciaux-eng` column exists per notice,
  naming exactly which trade agreements govern each tender's supplier
  eligibility — the mechanism that would let a future cycle determine
  Australian eligibility per-notice rather than guessing, if this
  source ever becomes reachable.

And then: `https://canadabuys.canada.ca/robots.txt`, read in full,
quoted verbatim above — two rule groups, `bingbot`/`Googlebot` get a
detailed, mostly-permissive rule set; every other user agent, including
this repository's own honest `titanos-cosmic-library-mouth/1`, hits
`User-agent: *` / `Disallow: /` — the entire site, including
`/opendata/pub/*.csv`, disallowed for anyone not claiming to be
Google or Bing. This is the same class of finding D-006 already
recorded for `data.gov.au` (blanket `Disallow: /`) and
`catalogue.data.govt.nz` (`Disallow: /api/`) — a deliberate publisher
choice, not a technical accident, and per this cycle's own rule
("NEVER spoof a User-Agent to defeat a WAF or robots.txt — blocked is a
finding, not an obstacle to route around") this source is **not used**,
despite the data itself being reachable at the HTTP layer with a
generic `curl` request. Presenting as `bingbot` to get past this would
be exactly the evasion the rule forbids.

## WHY NO MODULE WAS BUILT THIS CYCLE

None of the nine sources tested pass all five required conditions
(robots-clear, HTTP-reachable, open-shape, foreign-eligible,
security-work-present) simultaneously:

- **CanadaBuys** passes shape, eligibility-plausibility, and
  security-content — fails robots.
- **World Bank** passes robots and HTTP and eligibility-in-principle —
  fails shape (no reliable way to find currently-open notices).
- **GeBIZ** passes robots and HTTP — fails shape AND eligibility.
- Ireland, SAM.gov, UNGM, ADB/EBRD/EIB, NSPA, IDB all fail on "no
  reachable machine-readable open-opportunity feed exists" or an
  outright block, before shape/eligibility is even reachable as a
  question.

Per this repository's own Next-Lever Sequencer (`TITANOS_NEXT_LEVER_
SEQUENCER.md`) — a lower rung (build a new mouth) is not legitimate
while a higher rung (verify the critical assumption; here, "does a
buildable source exist") remains unresolved, and it resolved negative.
Building a `mouth_*.py` against any of the CANNOT rows would either
duplicate the wrong-shape mistake D-006 already named and rejected for
AusTender, or require exactly the User-Agent evasion this cycle's rules
explicitly forbid. **HOLD is the correct, valid result here** — see
`feedback_hold_is_a_valid_result.md`: a build-authorized task that
converges on no code is not a failure to report around, it is the
finding.

## WHAT WOULD CHANGE THIS

If CanadaBuys's `User-agent: *` disallow is ever narrowed (e.g. to
exclude `/opendata/`, which is exactly the kind of open-data carve-out
`data.gov.au` itself does NOT have but a policy team could plausibly
add), this is the strongest candidate in the entire route table by a
wide margin — reachable, open-shaped, real live security work,
permissive license. Re-check `canadabuys.canada.ca/robots.txt`
periodically rather than assuming this file's finding is permanent.
