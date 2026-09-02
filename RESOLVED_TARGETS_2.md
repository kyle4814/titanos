# RESOLVED_TARGETS_2.md

Second resolution pass, targeting the four opportunities `RESOLVED_TARGETS.md`
left as STILL UNRESOLVED. Same operator profile as that file: solo trader,
Australia, ABN, no certifications, no insurance, no corporate references, no
staff, English only.

Method actually used, all live, 2026-09-02: the UK Find a Tender Service's
own keyless OCDS Release Package API (`/api/1.0/ocdsReleasePackages/{ocid}`)
in place of the 403'ing HTML detail pages; the EU TED expert-search API
(`api.ted.europa.eu/v3/notices/search`, POST, via this repo's own
`foundation/mouth_ted.py`/`mouth_common.fetch_feed()` machinery and, for raw
per-field diagnosis, plain `curl` carrying this project's own honest,
declared User-Agent string `titanos-cosmic-library-mouth/1
(+https://github.com/kyle4814/titanos)` — never a spoofed browser UA); TED's
own PDF export of a full notice; and, for RTÉ, a real static document-download
URL pattern (`/epps/cft/downloadContractDocument.do?documentId=...`) read
directly out of the eTenders document-list page's own JavaScript source
(`location.href="/epps/cft/downloadContractDocument.do?documentId="+docId+...`)
rather than executing that JavaScript — the same "read the JS, don't run it"
discipline this repo's mouths already use for HTML card markup. No WAF was
evaded and no User-Agent was faked anywhere in this pass.

---

## 1. City of Bradford MDC — STILL UNREADABLE (one specific question only;
almost everything else is now resolved)

**VERDICT: STILL UNREADABLE** for the one critical question (CHECK/CREST
mandate). Every other fact about this notice is now resolved, live, from the
notice's own OCDS release package — the detail HTML page still 403s, but the
structured record behind it does not.

Source: `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-06e59c`,
fetched successfully (keyless, no login, no WAF block) and inspected as raw
JSON.

Resolved, verbatim from the OCDS record:

> `"title": "Ad-Hoc Application Penetration Testing and IT Health Checks (PSN) and Other Security Services"`

> `"description": "The Council is seeking to appoint a suitably experienced and qualified Provider (the Provider) to deliver These vulnerability tests must make use of both automated and manual testing and using best practice strategies from NCSC (National Cyber Security Centre), Open Web Application Security Project (OWASP) etc, to undertake our PEN testing. This tender is for the multiple block purchases of 10 consultancy days which can be used for a variety of security related testing and consultancy intended to identify weaknesses utilising publicly known vulnerabilities, common configuration faults or poor cyber awareness. Including our IT Health Check for PSN compliance (both Internally and Externally). The Council anticipates (but does not guarantee) that it will enter into a Framework Contract with the top 3 successful Providers. The Framework will be established as an Open Framework under the Procurement Act 2023. The initial framework term will be three (3) years, with the Authority intending to re-open the framework and award a successor framework before the expiry of the initial term..."`

> **`"tenderPeriod": {"endDate": "2026-09-14T16:00:00+00:00"}`** — the real submission deadline. **12 days from this pass's date (2026-09-02).** Not found in the prior pass at all.

> `"value": {"amountGross": 300327.0, "amount": 250273.0, "currency": "GBP"}`

> `"awardCriteria"`: Quality 40% (weight `percentageExact`), Social Value 10%, Price 50%.

> `"suitability": {"sme": true, "vcse": true}`

> `"contractPeriod": {"startDate": "2026-11-16T00:00:00Z", "endDate": "2034-11-15T23:59:59Z"}`, `"hasOptions": true`, `"options": {"description": "Open Framework - possible change of suppliers"}`

> `"submissionMethodDetails": "https://uk.eu-supply.com/app/rfq/rwlentrance_s.asp?PID=108256&TID100113322&B="` — the real submission portal, found this pass. Reached live: it is a session-cookie-establishing entrance page on the eu-supply.com platform (same platform family as `RESOLVED_TARGETS.md`'s RTÉ mirror) that 302-redirects to itself pending a cookie — not a WAF block, a normal session bootstrap a real browser handles automatically and `curl`/an automated fetch does not. No content was retrievable from it this way; not pursued further (see FIRST STEP).

**The CHECK/CREST question specifically — still unanswered.** The OCDS
record's own selection-criteria field is honest about not containing the
answer:

> `"selectionCriteria": {"criteria": [{"type": "economic", "description": "See tender documentation"}, {"type": "technical", "description": "See tender documentation"}]}`

Two document entries exist in the record: `"conflictOfInterest"` (marked
`"description": "Not published"`) and `"tenderNotice"` (points back to the
403'ing `find-tender.service.gov.uk/Notice/078110-2026` HTML page). No ITT
pack, specification document, or ZIP is exposed through the OCDS API — only
through the eu-supply.com portal above, which requires a live browser
session. The prose description above does not itself state a CHECK/CREST
mandate — it names NCSC/OWASP methodology, not an accreditation scheme — but
the actual conditions-of-participation document (where such a requirement
would conventionally sit) was not reachable this pass either.

**UNREADABLE — human must either (a) open
`https://uk.eu-supply.com/app/rfq/rwlentrance_s.asp?PID=108256&TID100113322&B=`
in a real browser (it will establish a session and proceed past the
redirect a bare fetch cannot complete), or (b) open
`https://www.find-tender.service.gov.uk/Notice/078110-2026` directly.**

**DEADLINE: 2026-09-14T16:00:00+00:00 UTC — 12 days from this pass.** This
is now a hard, real, close deadline, not "not found" as the prior pass had
it. If the CHECK/CREST question cannot be resolved quickly, the timing
itself is the binding constraint.

**FIRST STEP:** A human opens the eu-supply.com submission portal URL above
in a real browser (not a fetch tool) — the 302-self-redirect is a session
cookie handshake, not a block — and reads the actual ITT/specification
document for the CHECK/CREST question, with 12 days on the clock.

---

## 2. NHS England — RESOLVED: the notice is real, and access is gated

**VERDICT: CANNOT APPLY**, for a documented structural reason — not because
the notice doesn't exist (it does; the prior pass's "not locatable" finding
is corrected here) and not because of turnover/insurance (unknown), but
because of how this specific procurement is routed.

Source: `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-067639`,
fetched successfully, full OCDS 1.1 planning-stage release.

> `"tender": {"title": "Penetration Testing Services 2026-2030", "description": "This requirement is for new procurement for the provision of Penetration testing for a 4 year call off contract (2+1+1).  The procurement route is Crown Commercial Services' Cyber Security Services 3 Dynamic Purchasing System (DPS) - Ref RM3764. Penetration testing is required throughout various programmes, systems and services across NHS England and the wider NHS.", "status": "planned", "procurementMethod": "selective", "procurementMethodDetails": "Using pre-Procurement Act commercial tool"}`

> `"value": {"amountGross": 7200000.0, "amount": 6000000.0, "currency": "GBP"}` — the £7.2M figure in the original task brief is **confirmed real**, not fabricated.

> `"relatedProcesses": [{"id": "framework", "relationship": ["framework"], "title": "CCS - Cyber Security Services 3 - RM3764"}]`

> `"lots": [{"contractPeriod": {"startDate": "2026-10-28T00:00:00Z", "endDate": "2028-10-27T23:59:59+01:00", "maxExtentDate": "2030-10-28T23:59:59Z"}, "status": "planned"}]`

**Why this is CANNOT APPLY:** `procurementMethod: "selective"` via an
existing Crown Commercial Service Dynamic Purchasing System (RM3764, "Cyber
Security Services 3") means NHS England is not running an open competition
any outside operator can respond to directly — it is drawing down from
suppliers already admitted to CCS's own RM3764 DPS. This notice itself is
still `"status": "planned"` (a pipeline/planning-stage release, not yet a
live tender), and even once it moves to tender stage, participation
requires prior admission to RM3764. No document in this OCDS record states
RM3764's own admission criteria (turnover, insurance, technical capability)
— that lives on Crown Commercial Service's own site, not in this notice.

**DEADLINE:** contract start (estimated) 28 October 2026; this is a planning
notice, no submission deadline is yet published for this specific
call-off.

**FIRST STEP:** the real path into this specific £7.2M opportunity is not
this notice — it is Crown Commercial Service's RM3764 "Cyber Security
Services 3" DPS itself. A human should check whether RM3764 is a rolling
DPS still open to new supplier applications (DPSs conventionally are, for
their duration) at Crown Commercial Service's own site — not investigated
this pass, genuinely out of this pass's scope, and the honest next physical
step rather than a guess.

---

## 3. RTÉ Ireland (25P041) — RESOLVED

**VERDICT: CANNOT APPLY.** The actual ITT document was reached and read in
full this pass — not a snippet, the real `.docx`.

**How it was reached, for the record (the prior pass's blocker is now
closed):** the document-list page's own JavaScript
(`onclick="downloadDocForAnonymous('6761578')"`, calling
`location.href="/epps/cft/downloadContractDocument.do?documentId="+docId+"&resourceId=6565390"`)
was read as text, not executed, to recover the real static download URL:
`https://www.etenders.gov.ie/epps/cft/downloadContractDocument.do?documentId=6761578&resourceId=6565390`.
That URL returned HTTP 200 with `Content-Disposition: attachment;
filename="25P041 RTÉ Cyber Security DPS v3.0 Revised.docx"` — the exact file
`RESOLVED_TARGETS.md` named as existing-but-unreachable. Downloaded and
parsed (129,029 bytes, real Word XML). Independently corroborated by TED
notice 612163-2025 (see below), reached via this repo's own
`foundation/mouth_ted.py`-style query against `api.ted.europa.eu`.

Verbatim from the ITT document (`25P041 RTÉ Cyber Security DPS v3.0
Revised.docx`):

> "P2 Financial and Economic Standing Tenderers must have achieved a minimum turnover level of €350,000 in each of the three (3) previous financial years."

> "P3 Minimum Insurance Requirements Tenderers must maintain the following minimum levels of insurance cover: Public Liability €6.5M Cyber Insurance €1.0m Professional Liability €1.0m Employer's Liability €13M"

> "P4 Staff Resources Please provide details of the average overall annual staff employed by the Tenderer over the past three years. Please provide details of the number of managerial staff over the past three years. Please provide details of the number of staff per discipline (appropriate to your business) over the past three years. Tenderers must be in a position to demonstrate that it has sufficient overall staffing to manage contracts similar to those required to meet the Specification."

> "Tenderers are restricted to a maximum of three referenced projects in total, any further projects will be excluded from marking."

> Scoring gate structure: "P1 Eligibility Pass/ Fail P2 Financial and Economic Standing Pass/ Fail P3 Minimum Insurance Requirements Pass/ Fail P4 Staff Resources Pass/ Fail P5 Quality Assurance Pass/ Fail P6 Health, Safety and Welfare at Work Assurance Pass/ Fail" — every one of these is a binary gate, not a scored criterion; failing any one eliminates the tender before quality/price is even considered.

**Same disqualification shape as ECHA (Helsinki) in `RESOLVED_TARGETS.md`:**
a bare solo trader with no staff, no track record, no existing insurance
cover fails P3 and P4 outright (and likely P2, turnover), before P1
eligibility or the technical questions are even reached.

Corroborating structured data, TED notice 612163-2025 (fetched via
`api.ted.europa.eu/v3/notices/search`, and independently via the notice's
own official PDF export at `https://ted.europa.eu/en/notice/612163-2025/pdf`):

> "Type of procedure: Restricted" — a two-stage process (expression of
> interest / PQQ first, then invited to tender), confirmed by "Minimum
> number of candidates to be invited for the second stage of the
> procedure: 1".

> "Deadline for receipt of requests to participate: 30/10/2030 13:00:00
> (UTC+01:00)" — this is the DPS's own long-running admission window, not a
> near-term cutoff (matches the task brief's stated 19 Sep 2025 – 30 Oct
> 2030 run).

> "Estimated value excluding VAT: 7 500 000,00 EUR" across all 3 lots
> combined; "The tenderer must submit tenders for all lots" (all 3, not a
> choice).

> "Sources of selection criteria: Procurement Document" / "Sources of
> grounds for exclusion: Procurement Document" — TED's own record confirms
> the real criteria live only in the ITT document, which is exactly the
> document read directly above; this is not a second unresolved gap.

**DEADLINE:** DPS admission window runs to 30/10/2030 — not urgent by
timing; the disqualification is structural (turnover/insurance/staff), same
as ECHA.

**FIRST STEP:** moot given the verdict. If the operator's profile changes
(incorporated, insured, staffed, ≥€350k turnover for 3 years), the real
application path is
`https://www.etenders.gov.ie/epps/cft/viewTenders.do?resourceId=6565390`.

---

## 4. EU Commission DG DIGIT (TED 773405-2024) — RESOLVED

**VERDICT: CANNOT APPLY** — confirmed out of scope by the notice's own text,
not by the title-only inference `RESOLVED_TARGETS.md` flagged as
unconfirmed. That flag is now confirmed.

Source: `api.ted.europa.eu/v3/notices/search`, queried live by
publication-number (`publication-number IN ("773405-2024")`) via this
project's own honest User-Agent — the TED API itself, not the Mercell
portal or the TED Angular SPA either of which blocked the prior pass.

> `"notice-title"` (eng): "Belgium – Computer equipment and supplies – Dynamic Purchasing System (DPS) for IT Supplies"

> `"description-proc"` (eng): "Acquisition of all types of end-user IT hardware equipment, including cybersecurity equipment and datacentre infrastructure equipment. The DPS will also include related services, such as warranty and extended guarantee services of different levels and other additional services associated to the equipment in scope, as well as standard contract management services."

This is a **hardware/equipment procurement DPS** — end-user IT hardware,
datacentre infrastructure equipment, warranty/guarantee services — not a
penetration-testing or security-consultancy services contract. The prior
pass's "Flag, not a finding" inference from the title alone
("IT Supplies... conventionally denotes hardware/goods delivery... this is
an inference from the title only, unconfirmed from the notice body") is now
confirmed directly from the notice body: out of scope for a security
consultant regardless of any financial/turnover threshold.

Per this task's own method note, the selection-criterion field was also
checked directly, in case scope were somehow ambiguous:

> `"selection-criterion-description-lot"` (eng): `["Please consult the procurement documents.", "Please consult the procurement documents.", "Please consult the procurement documents."]`

TED does not expose the numeric criteria for this notice either — same as
DG DIGIT's Mercell portal (still login-walled, not re-tried this pass since
the scope mismatch alone is decisive) — but the scope finding above already
settles the verdict without needing that number.

**DEADLINE:** not re-checked — moot given scope mismatch.

**FIRST STEP:** none — this opportunity is not a match for a security
consultancy offering regardless of eligibility, confirmed from the notice's
own text rather than assumed.

---

## SUMMARY TABLE

| # | Target | Verdict | Deadline | Key finding this pass |
|---|---|---|---|---|
| 1 | Bradford MDC | STILL UNREADABLE (one question only) | **2026-09-14T16:00 UTC — 12 days** | Full description/value/award-criteria/contract-period resolved via OCDS API; CHECK/CREST requirement specifically still locked behind a session-cookie-gated eu-supply.com portal, not a WAF |
| 2 | NHS England | CANNOT APPLY | Planning stage, no submission deadline yet | Notice is real (£7.2M confirmed); access is gated through Crown Commercial Service's existing RM3764 DPS, not an open competition |
| 3 | RTÉ Ireland 25P041 | CANNOT APPLY | DPS admission window to 30/10/2030 (not urgent) | Full ITT read: turnover ≥€350k×3yr, Public Liability €6.5M + Cyber €1.0m + Professional €1.0m + Employer's €13M insurance, staffing evidence, all Pass/Fail gates |
| 4 | EU DG DIGIT 773405-2024 | CANNOT APPLY | Not checked (moot) | Confirmed from notice body: an IT hardware/equipment DPS, not a security-services contract |

**Net effect of this pass:** two genuine new CANNOT APPLY verdicts closed
with real evidence (NHS England, DG DIGIT), one CANNOT APPLY confirmed with
the actual ITT document in hand for the first time (RTÉ), and one target
resolved from "nothing readable" to "everything readable except one
specific fact, with a hard 12-day deadline now known" (Bradford). The
technique that did the work in every case was the same: prefer a source's
own structured/API layer (OCDS release packages, TED's notice-search API,
TED's PDF export, a document-list page's own JavaScript revealing a static
download URL) over its JS-rendered or WAF-fronted HTML — never bypassing an
access control, only routing around JavaScript rendering to a plain HTTP
resource the same server already serves to anyone who asks correctly.
