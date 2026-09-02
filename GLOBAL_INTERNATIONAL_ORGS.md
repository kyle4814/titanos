# Global international organisations — can a PERSON register, or only a COMPANY?

STATUS: RESEARCH RECORD, NOT A BUILD. No module written, no `.py` file
touched, nothing committed, nothing registered.
DATE: 2026-09-03

## SCOPE AND METHOD

This is the eligibility question `docs/DECISIONS/D-007-new-sources.md`
explicitly left unanswered. D-007 checked UNGM/ADB/EBRD/EIB once for a
**machine-readable no-login feed** and recorded "no feed found" —
that is a reachability verdict about automated harvesting, not an
eligibility verdict about whether an Australian individual, ABN, no
certifications, no insurance, no corporate references, can register as
a human and win work. This file answers the eligibility question only.
It does not reopen or contradict D-007's feed-reachability finding.

Every claim below is either (a) quoted or closely paraphrased from a
live fetch made this session (marked **VERIFIED**, with the URL), or
(b) explicitly marked **UNKNOWN** because no live source was found or
the page was unreachable. Nothing is asserted from memory as if it were
a checked fact. `robots.txt` was read first for every domain touched;
no User-Agent was spoofed anywhere in this session — every fetch
identified honestly (`cosmic-library-research/1.0`, or the WebFetch
tool's own agent string). No registration was created, no form
submitted, no account made, per the task's own rules.

---

## 1. UNGM — United Nations Global Marketplace

**robots.txt** (`ungm.org/robots.txt`, read in full): the blanket
`User-Agent: *` block only disallows specific document/asset paths
(`/UNUser/Documents/*`, `/Styles/`, `/Scripts/`, etc.) — it does **not**
block `/Account/Registration/Individual`. A second block, scoped only
to named search-engine bots (Bingbot, Googlebot, etc.), separately
disallows `/Account/Registration/Individual` from being *indexed* — that
is a "don't index this page in search results" instruction, not a
"don't let a human visit it" instruction, and it does not apply to a
generic identified fetch.

**Individual registration — VERIFIED**, live fetch of
`https://www.ungm.org/Account/Registration/Individual`:

> The page hosts an "Individual Consultant account creation" form.
> Under "Individual Consultant Type" the options are: **Individual
> Consultant**, **Landlord**, **Sole proprietor**, **Other**.
> Requirements shown: contact email, password, and acknowledgment of
> "the UN Supplier Code of Conduct as the minimum standards expected of
> Individual Consultants to the United Nations."

**This directly answers the decisive question for UNGM: yes, a person —
not a company — can create a UNGM account, explicitly including a
"Sole proprietor" category**, which is exactly this operator's ABN
structure.

**Cost**: UNKNOWN — the registration page itself does not state a fee,
and no live source this session confirmed free-vs-paid. (UNGM's public
reputation is that Level 1 registration is free and higher tiers/tender
access may require a fee, but that specific claim was not verified
against a live page this session — do not treat it as confirmed.)

**Level 1 requirements**: UNKNOWN in detail — the registration form
itself was reached and read, but the full Level 1 requirement checklist
(country/UNSPSC codes, references, etc.) was not fetched this session.
Next step if this is pursued: fetch the vendor-guide/FAQ pages linked
from the registration flow once logged in.

**Does the UN buy security consultancy, and from whom**: UNKNOWN this
session specifically for UNGM's own notice board — D-007 already found
this class of content live on **CanadaBuys** (a different, non-UN
source, itself blocked by `robots.txt`) but did not check UNGM's own
notice content for security/pentest work; that check was not repeated
here. Flag as an open item, not asserted either way.

**Net finding for UNGM**: the shared UN registry explicitly has an
individual/sole-proprietor registration path, with no incorporation
requirement visible on the form itself. This contradicts D-007's own
earlier implicit framing (a "no feed found" verdict was never a "no
individual pathway" verdict) — UNGM is now confirmed as
individual-eligible at the registration layer, even though D-007's
separate finding (no public API/RSS, full detail gated behind
registration) still stands and is not disputed here.

---

## 2. UNDP / UNICEF / WFP / UNOPS — the priority item

### UNOPS — Individual Contractor Agreement (ICA)

**robots.txt / reachability**: `unops.org/robots.txt` is fully
permissive for a generic agent (only `/cpresources/`, `/vendor/`,
`/.env`, `/cache/`, `/search` disallowed). `jobs.unops.org` (UNOPS's
careers/recruitment portal, where individual contractor postings live)
returned HTTP 200 with no `robots.txt` restriction found.

**Blocker hit**: `jobs.unops.org` is a JavaScript single-page
application — every path fetched this session (`/`, `/how-to-apply`,
`/faq`, `/what-we-offer`) returned the identical 555-line SPA shell with
no server-rendered job/policy content, and `unops.org/policies`,
`/business-opportunities/how-we-procure`, and every guessed static ICA
URL either 404'd or came back with only navigation boilerplate (no ICA
policy text, confirmed by scanning WebFetch's own text extraction of
those pages). **The existence and mechanics of the ICA modality named in
this task's own brief — "a UN mechanism designed for people, not
companies" — could not be independently confirmed or quoted from a live
UNOPS page this session.** This is a real gap, not a soft-pedalled
"probably fine": mark UNOPS's ICA modality **UNKNOWN (mechanics)**,
**VERIFIED (portal exists, reachable, not blocked)**.

What is verified: `jobs.unops.org`'s own homepage copy states UNOPS
recruits "more than 6,000 personnel recruited on behalf of our
partners" alongside 5,000+ staff, across 130+ countries — consistent
with (but not proof of) a large individual-contractor population, since
that sentence does not itself distinguish staff from ICA holders.

**What would resolve this**: the ICA modality is a real, named,
long-standing UNOPS HR mechanism (Individual Contractor Agreement,
governed by UNOPS Personnel Instructions) — but every attempt to reach
the actual policy document or a plain-language "how ICAs work" page
this session hit either a 404 or the unreadable SPA shell. If this
becomes a live build target, the next concrete step is not another
guess at a URL — it's asking UNOPS's own published contact channel
(`procurement@unops.org` is for vendors, not ICAs; the correct channel
is the careers/HR helpdesk linked from the SPA, not independently
resolved this session) or finding the UNOPS Personnel Instruction PDF by
its formal document number rather than by URL-guessing a slug.

### UNICEF — VERIFIED: Consultant is a distinct advertised contract type

Live fetch, `https://jobs.unicef.org` (robots.txt fully permissive for
`*`, only admin/staging/login paths disallowed):

> The vacancy search filter "Contract type" lists exactly four options:
> **Consultant**, Fixed Term Appointment, Internship, Temporary
> Appointment.

**Consultant is filterable as its own contract type, separate from
staff appointments.** This confirms UNICEF advertises individual
consultancy work through its own public jobs portal, openly, with no
login required to browse. It does not by itself confirm eligibility
rules (nationality, company-vs-individual) for a Consultant listing —
those live on each individual vacancy notice and were not fetched this
session (would require picking a specific live listing).

### UNDP

`jobs.undp.org` returned HTTP 403 to an honestly-identified fetch this
session — **blocked**, same class of finding as D-007's WAF-blocked
Australian sources, not evaded. `procurement-notices.undp.org/robots.txt`
is a blanket `Disallow: /` for all agents — also respected, not evaded.
**UNDP's individual-consultant eligibility mechanics: UNKNOWN this
session** — both of its two most relevant public portals were closed to
an honest fetch.

### WFP

`jobs.wfp.org` did not resolve (curl exit code timeout/DNS, recorded as
`000`) this session. `wfp.org/robots.txt` itself is permissive, but the
specific careers subdomain could not be reached. **UNKNOWN this
session** — not blocked by policy, just not successfully reached; worth
a retry, not written off as CANNOT.

### Net finding for item 2

**UNICEF is the one live-verified case this session where "Consultant"
is a first-class, browsable, individual-oriented contract category on a
fully reachable public portal.** UNOPS's ICA modality — named in the
brief as possibly the single most relevant finding in this whole task —
remains **structurally plausible and reachable at the portal level, but
mechanically unverified**, because its real content sits behind a JS SPA
this session's tooling could not render. UNDP is blocked; WFP is
unreached. This is the strongest concrete "come back and try harder"
item in this file, not a dead end: the portal is not blocked, it just
needs either a JS-capable fetch or the specific UNOPS Personnel
Instruction document located by its formal reference.

---

## 3. World Bank — Individual Consultants

**robots.txt**: `worldbank.org` and `projects.worldbank.org` both
permissive for a generic agent.

**Blocker hit, same shape as UNOPS**: every guessed URL for a
"Individual Consultants" procurement-framework page (roughly 15 URLs
tried, spanning `worldbank.org`, `projects.worldbank.org`,
`policies.worldbank.org`, `thedocs.worldbank.org`) either 404'd or
landed on generic navigation-only content with the substantive policy
text not present in what was fetched. `www.worldbank.org/en/about/careers`
is staff-jobs-only and explicitly does not cover the Individual
Consultant category (checked live — the careers page's own content has
"Search Open Positions," "Talent Programs," etc., no consultant-roster
material). The old dedicated procurement micro-site
(`projects.worldbank.org/.../products-and-services`) now 302-redirects
to a generic "what we do" page with a banner stating the old
project-procurement content "has been transferred to our new dedicated
website" — but that new destination's actual Individual Consultant
content was not located this session.

**Net finding: World Bank's Individual Consultant category — real,
named in the Bank's own published Procurement Framework
(`Selection of Individual Consultants` is a standard, well-known method
alongside firm-based selection) — could not be independently confirmed,
quoted, or sourced to a live page this session.** Mark this **UNKNOWN**,
not CANNOT. This directly echoes D-007's own earlier World Bank
finding (`search.worldbank.org/api/procnotices` is reachable,
unauthenticated, real, but has no reliable way to isolate
currently-open notices) — the pattern across both cycles is the same:
World Bank's *data* is open and unblocked, but its *documentation
structure* is hard to hit with URL-guessing and no search tool. A
future session with either a working search budget or the exact
document reference (the current Procurement Regulations for IPF
Borrowers, Section on individual consultants) would resolve this
quickly; guessing slugs did not.

---

## 4. Asian Development Bank — CMS, individual consultants

**This is the strongest, fully-verified finding in this file.**

**robots.txt**: `adb.org` permissive for a generic agent (only CSS/JS
asset caching directives). `cms.adb.org` redirects (302) to
`selfservice.adb.org` — reached without incident.

**VERIFIED, live fetch of
`https://www.adb.org/business/how-to/how-can-i-become-adb-consultant`**
(title: *"How can I become an individual ADB consultant?"*):

> "ADB engages individual consultants and consulting entities (firms,
> universities, NGOs, etc.) for a wide range of assignments. Individuals
> wishing to consult for ADB must meet all of the following criteria:
> - Be a citizen of an **ADB member country**
> - Not be **barred** from working with ADB, World Bank or ADB's member
>   countries
> - Not be a close family member (other than spouse) of an ADB employee"

> "Next steps: Search Projects and Tenders to see if there are
> consulting opportunities for which you are qualified... Do you meet
> the criteria? **Register as a consultant in ADB's Consultant
> Management System.**"

**Australia is a full ADB member country** (ADB was founded in 1966
with Australia as a founding member — this is public, uncontested
fact, not re-verified against a live ADB membership-list page this
session, but not in serious doubt). **An Australian individual with no
company, no certifications, no insurance therefore meets ADB's stated
individual-consultant eligibility bar on its face** — the criteria list
above contains no incorporation requirement, no insurance requirement,
no minimum-turnover requirement, no reference requirement. This is the
sharpest structural contrast in this whole file against the
€13M-insurance / three-corporate-reference / €2.6M-turnover barriers
named in the task brief: **ADB's own published individual-consultant
criteria contain none of them.**

**VERIFIED, live fetch of
`https://www.adb.org/business/how-to/what-consultant-management-system`**:

> "The Consultant Management System or CMS (http://cms.adb.org/) is an
> online system where ADB does the following: advertise consulting
> services recruitment notices (CSRNs); recruit consultants; manage
> contracts and framework agreements; process consultants' performance
> evaluation." Consultants can, via CMS: "register in ADB's consultant
> database, create and update their profile, search opportunities,
> prepare and submit expressions of interest, respond to non-committal
> inquiries (NCIs) or request for proposals (RFP), prepare and submit
> proposals, respond to contract offers, submit timesheets and
> deliverables, submit claims and advance request, provide feedback."
> "Access to the system is gained by typing a registered email address
> and password."

**Contrast confirmed against the firm-side page**
(`how-can-my-company-consult-adb`, also fetched live): firms must be
"legal entities," "incorporated, registered, or legally established in
an ADB member country," and hold "a bank account for financial
transactions" — none of which apply to the individual page above. ADB's
own site structure treats individuals and firms as genuinely separate
tracks with separately stated, separately lighter requirements for
individuals.

**Registration cost**: not stated on either page fetched — UNKNOWN, but
no fee is mentioned anywhere in the individual-consultant flow (in
contrast to some national/state portals this campaign has already hit
that charge a supplier-registration fee).

**Net finding: ADB is the single cleanest, fully-verified example in
this task of an individual-consultant modality with no company
requirement, reachable without a WAF block, with the exact eligibility
rule quoted from a live page.**

---

## 5. NATO, OSCE, OECD, Council of Europe, IAEA

- **NATO**: `nato.int/robots.txt` itself is permissive, but D-007
  already found NATO's actual procurement arm, **NSPA**
  (`nspa.nato.int`), returns a Cloudflare bot-challenge (403,
  `cf-mitigated`) before `robots.txt` can even be read — not evaded, per
  standing rule. Not re-tested this session; D-007's finding stands.
  **Open calls an individual can answer: UNKNOWN/CANNOT (blocked at the
  network layer before eligibility is reachable as a question).**

- **OSCE**: `osce.org` and `jobs.osce.org` both fully reachable,
  `robots.txt` permissive. **VERIFIED, live fetch of
  `jobs.osce.org`**: the front page lists staff positions, secondment
  jobs, a Junior Professional Officer programme, internships — no
  "Consultant" or individual-contractor filter category was visible in
  the page content fetched (contrast with UNICEF's explicit
  "Consultant" filter, above). This does not prove OSCE never engages
  individual consultants (many international bodies do so ad hoc,
  outside the main vacancy portal), but no open, individual-oriented
  call mechanism was found live this session. **UNKNOWN/weak-NO** for a
  standing open-call mechanism; not investigated further (e.g. no
  specific vacancy notices were opened).

- **OECD**: `oecd.org/robots.txt` permissive, but
  `www.oecd.org/careers` returned **HTTP 403** to an honest fetch this
  session — blocked, not evaded. **UNKNOWN/blocked.**

- **Council of Europe**: `coe.int/robots.txt` itself returns a
  Cloudflare "Attention Required — you have been blocked" challenge
  page (same class as `unicef.org`'s main domain, D-007's
  `nspa.nato.int` finding, and this task's own note about WAF blocks
  being a finding, not an obstacle to route around). **Blocked, not
  evaded. UNKNOWN.**

- **IAEA**: `iaea.org/robots.txt` permissive, but
  `iaea.org/about/employment` returned **HTTP 403**. The IAEA's
  recruiting system (`iaea.taleo.net`) returned 200 but is a
  JavaScript-redirect shell with no static content reachable this
  session — same class of blocker as UNOPS's careers SPA above.
  **UNKNOWN.**

**Net finding for item 5: of five organisations, only OSCE's own portal
was actually readable, and it showed no individual-consultant-specific
call mechanism live. The other four are blocked, 403'd, or JS-opaque —
none confirmed open to an individual this session, none confirmed
closed either. This is a real gap, not a soft "probably no."**

---

## 6. EU institutions — framework contracts and expert rosters beyond TED

`ec.europa.eu/robots.txt` permissive for a generic agent (only a few
legacy paths disallowed). The EU Funding & Tenders Portal's "Experts"
section (`ec.europa.eu/info/funding-tenders/opportunities/portal/screen/
how-to-participate/experts`) returned HTTP 200 and is reachable — but,
like UNOPS careers and IAEA's Taleo system, it is a JavaScript
single-page application; the fetch this session returned only the page
title ("EU Funding & Tenders Portal") with no rendered eligibility text.

**Net finding: UNKNOWN.** The EU expert-database mechanism (individuals
registering to evaluate proposals, monitor projects, sit on expert
panels — a well-known, long-standing EU mechanism, distinct from TED's
procurement-notice feed D-007 already covers) is reachable at the
network layer but its actual registration rules were not captured live
this session because of the SPA rendering problem that recurred at
UNOPS, IAEA, and here. **Not confirmed open to an individual, not
confirmed closed — genuinely unresolved**, and the most repeated single
technical blocker in this whole file (three of six sections hit the
same "JS SPA, no server-rendered content" wall: UNOPS, IAEA, EU
experts).

---

## SUMMARY TABLE

| Organisation | Individual/sole-trader path exists? | Evidence |
|---|---|---|
| UNGM | **YES** — "Individual Consultant" / "Sole proprietor" account type on the live registration form | VERIFIED (quoted) |
| UNOPS (ICA) | Portal reachable, not blocked; mechanics unconfirmed | UNKNOWN (SPA blocker) |
| UNDP | Blocked (403 / blanket robots disallow) | BLOCKED, not evaded |
| UNICEF | **YES** — "Consultant" is a distinct, filterable contract type on the open careers portal | VERIFIED (quoted) |
| WFP | Not reached (DNS/timeout) | UNKNOWN |
| World Bank (Individual Consultants) | Real named category in Bank policy; live page not located | UNKNOWN |
| ADB (CMS) | **YES** — quoted individual-consultant criteria, no incorporation/insurance/turnover requirement, Australia is a member country | VERIFIED (quoted, strongest finding) |
| NATO (NSPA) | Blocked at network layer | BLOCKED (per D-007, not re-tested) |
| OSCE | Portal reachable; no individual-consultant call mechanism visible | UNKNOWN/weak-NO |
| OECD | Blocked (403) | UNKNOWN/blocked |
| Council of Europe | Blocked (Cloudflare challenge) | UNKNOWN/blocked |
| IAEA | Blocked (403) / SPA opaque | UNKNOWN |
| EU expert rosters (beyond TED) | Portal reachable; rules not rendered (SPA) | UNKNOWN |

## THE DECISIVE ANSWER

**Two organisations this session fully confirms, by direct quote from a
live page, have a real individual-registration path with no
incorporation requirement: UNGM (system-wide UN registry) and ADB
(Consultant Management System).** ADB's is the sharper of the two — its
own site draws an explicit individual-vs-firm line and states the
individual criteria in full (citizenship of a member country, not
barred, not a close relative of an ADB employee — nothing else),
directly naming Australia-eligibility by virtue of Australia's ADB
membership. UNICEF adds a third confirmed case at the advertising
layer (Consultant is a first-class browsable contract type).

**The task's own hypothesis — that an individual-consultant modality
structurally removes the local-entity/insurance/turnover barriers that
have blocked this campaign everywhere else — is directly supported by
what was actually quoted this session, not merely plausible.** The
remaining gaps (UNOPS's ICA mechanics, World Bank's exact page, three
of five item-5 bodies, EU's expert-roster rules) are genuine unresolved
items caused mostly by one recurring technical wall — JavaScript
single-page portals that a static/text-mode fetch cannot render — not
by any eligibility finding against the individual pathway. No barrier
of the €13M-insurance/three-corporate-reference/€2.6M-turnover shape
was found anywhere in this file's individual-consultant pages; where
detail was unreachable, it was unreachable for a technical reason
(SPA, 403, DNS), never because a rule was found and it excluded a
solo operator.

## WHAT WOULD RESOLVE THE REMAINING UNKNOWNS

1. **UNOPS ICA mechanics** — locate the actual UNOPS Personnel
   Instruction on Individual Contractor Agreements by its formal
   document number (not by guessing URL slugs against a JS SPA), or use
   a JS-capable fetch against `jobs.unops.org`.
2. **World Bank Individual Consultants** — same problem, different
   cause (URL-guessing without a working search tool). The Bank's
   current Procurement Regulations for IPF Borrowers document is the
   right target; find it by exact title/reference rather than guessed
   path.
3. **NATO/OECD/Council of Europe/IAEA** — all blocked or 403'd this
   session; per this repository's own standing rule, do not evade with
   a spoofed User-Agent. Re-check periodically (robots/WAF posture
   changes, as D-007 itself notes for CanadaBuys).
4. **EU expert rosters** — same JS SPA wall as UNOPS/IAEA; a
   JS-capable fetch would likely resolve this quickly since the portal
   itself is fully reachable (200, permissive robots.txt).

No further action was taken this session beyond recording the above —
per the task's own rules, nothing was registered, no form was
submitted, and no account was created anywhere.
