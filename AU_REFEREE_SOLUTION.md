# AU Referee-Report Blocker — Findings and Path Through

Answers the one blocker flagged in `AU_PANEL_CHECKLIST.md` §1.6: NSW ICT
Services Scheme Rules §8.1 requires **two (2) referee reports** for the
K03 category, and the operator has no corporate references and no prior
public-sector contracts. Every quote below was read directly out of the
primary-source document text (extracted from the actual `.docx` files,
not summarised from a search snippet), fetched 2026-09-02. Where a
document was not reachable without spoofing a browser, that is stated
explicitly rather than guessed at.

Documents fetched and read directly:
- Scheme Rules v2.2, August 2023 —
  `https://www.info.buy.nsw.gov.au/__data/assets/word_doc/0005/589136/ict-services-scheme-rules-august-2023_v2.docx`
- Summary of ICT Services Scheme Membership Requirements, September 2024 —
  `https://www.info.buy.nsw.gov.au/__data/assets/word_doc/0003/1325793/Summary-of-ICT-Services-Scheme-Membership-Requirements.docx`

---

## Q1 — What must a referee report contain, and who may give one?

**Quoted, in full, everywhere the Scheme Rules mention referees** (there
are exactly two occurrences, both in the §8.1 admission-requirements
table):

> "two (2) referee reports for each nominated high-level category"
>
> "Note: can be the same referees for multiple categories if applicable."

That is the entire text. The Scheme Rules' own **Definitions** section
(section 2, checked in full) does **not define "Referee"** as a term —
it is not a defined word anywhere in the document. There is no clause
anywhere in the Scheme Rules or the Summary FAQ stating a referee must
be a past *paying* customer, a government agency, or a corporate entity.
**The eligibility of a referee is not addressed at all in either public
document.** This is a genuine silence in the primary source, not a
gap in this research.

**The actual K03 referee-report form/template is not publicly
reachable.** A search surfaced `SCM5841_Referee Report TEMPLATE.docx` on
`tenders.nsw.gov.au`, specifically for this scheme — fetching it
returned a CloudFront **403 Forbidden** ("Request blocked"), the same
WAF pattern `AU_PANEL_CHECKLIST.md` already documented for AusTender and
the state portals. Per this task's rules, no User-Agent was spoofed to
get past it. **This form is only visible after Supplier Hub login** (or
after DCS emails it as part of the application flow) — confirmed
genuinely inaccessible publicly, not merely unsearched.

**One structural data point, clearly labelled as inference, not proof**:
a separate NSW prequalification scheme (Employment Related Medical
Services — a different scheme, not ICT Services) publishes its own
"Schedule 6: Referee Report" template publicly, and it *was* fetchable.
Its shape, for context only (do not treat this as the K03 form):
- Part A, completed by the applicant: business name, contact, phone,
  description of services provided, dates services commenced/completed,
  **indicative fee for services** ($ field present).
- Part B, completed by the referee: comments against the applicant's
  nominated capabilities.
- Part C: a rating scale (Unsatisfactory/Acceptable/Good/N/A) against
  Time Management, Experience, Standard of Service, Quality Outcomes,
  Cost, Value for Money, Communications.
- Explicit rule: **"This Referee Report must be signed or it will not
  be considered to be a completed report."**
- Explicit recency window for that scheme: **"engagement/s provided or
  completed in the last 18 months."**

This is the same document family/publisher (`info.buy.nsw.gov.au`,
"Schedule 6" naming convention) as the ICT scheme, so it is a reasonable
guide to what the K03 form will structurally resemble — a signed,
letterhead-bearing statement from someone the applicant actually did
paid or unpaid work for, rating capability against named criteria — but
it is **not evidence of the ICT scheme's own recency window or
specific fields**, which remain unconfirmed until the K03 form itself is
seen (post-login).

**Direct answer to "must the referee be a past paying customer, or can
it be any professional who can attest to capability?"**: **Unconfirmed
by the public Scheme Rules — genuinely silent, not "no."** Nothing in
the primary source restricts referees to paying customers. The
analogous form's fee field appears to be describing the engagement, not
gatekeeping payment as a precondition — but this is inference, not a
quoted rule, because the actual field-level instructions for K03 have
not been seen.

## Q2 — Can private-sector clients, pro-bono work, open-source
contributions, or bug-bounty disclosures serve as referees? Any stated
exclusion?

**No exclusion of any kind is stated anywhere in the Scheme Rules or the
Summary FAQ.** Confirmed by full-text search of both documents for
"private," "government," "corporate," "paying," "volunteer," and
"pro bono" in referee context — none of these words co-occur with
"referee" anywhere in either document. A private-sector client
reference is not excluded by the text. Pro-bono/volunteer/open-source/
bug-bounty referees are similarly not excluded by the text — but they
are also not explicitly included, since the Rules simply don't discuss
referee eligibility at all. **This is the single most important finding
of this research**: the operator's assumption ("no corporate references
= disqualifying") is not supported by anything in the public Scheme
Rules. The real test is whatever the login-only referee form itself
asks the referee to attest to (which the analogous form suggests is:
capability, timeliness, quality, communication — not "are you a
government agency" or "did money change hands").

**Action needed, cheap and low-regret**: email
`ICTServices@customerservice.nsw.gov.au` (the scheme's own listed
contact for exactly this kind of question, used throughout the Scheme
Rules for reviews and category changes) and ask directly: "Can a
referee report be provided by a private-sector client, a documented
pro-bono engagement, or a party who received a responsible-disclosure
report from us, rather than a government or corporate client?" This is
a five-minute email to the primary source, not a guess.

## Q3 — Is there a new-entrant / start-up / no-trading-history pathway?

**No. Confirmed absent, not merely unfound.** Both documents were
searched in full for: "new entrant," "start-up," "start up," "trading
history," "newly established," "newly registered." **Zero matches in
either document.** The only start-up-adjacent accommodation anywhere in
either source is insurance-related, not referee-related — the SME
insurance deferral under PBD 2023-03 (already documented in
`AU_PANEL_CHECKLIST.md` §1.2) has no counterpart for referees. NSW's
ICT Services Scheme has no stated new-supplier waiver for the two-referee
requirement. This is a real, confirmed gap in the scheme, not an
assumption.

## Q4 — What happens if you apply with fewer than two referees?

Not addressed as its own explicit rule (no clause specifically says "an
application with 0 or 1 referee reports will be X"), but two general
rules bound the answer:

> "Acceptance on the Registered Supplier List and Advanced Registered
> Supplier List is subject to: provision of all required information;
> agreement to these Scheme Rules; and confirmation of Supplier
> Declaration."

Since two referee reports are listed as required §8.1 information, an
application missing them fails "provision of all required information"
— the likely practical outcome is **rejection for that category**, not
an automatic "please provide more info" hold. This reads alongside the
Rules' own disclaimer:

> "DCS and the ICT Services team reserve the absolute discretion to:
> accept or reject an Application with or without limitations and/or
> conditions"

**Is it re-submittable?** Yes — the scheme is explicitly open-ended
(*"The ICT Services Scheme is open continuously and for an indefinite
period"*), and the Rules provide a formal review path for a rejected
application:

> "Should an Application be unsuccessful, the Applicant may ask for the
> decision to be reviewed by the ICT Services team if they believe there
> is substantive grounds for reconsideration... A review request must be
> made in writing via email to ICTServices@customerservice.nsw.gov.au,
> providing full details of the reasons for the request."

Nothing in the Rules bars simply re-applying once two referees are in
hand, either via the review path or a fresh application. **Exact
mechanics of "apply again after a referee-driven rejection" are not
spelled out** — genuinely unknown until tested or asked directly (same
email address covers this).

## Q5 — Other Australian routes: how hard is their reference requirement?

Ranked softest to hardest, using only what was **directly and
successfully fetched** this cycle (not inferred from search snippets):

| Rank | Route | Reference/referee requirement | Evidence |
|---|---|---|---|
| 1 (softest, tied) | **ICN Gateway** | **None found.** FAQ page fetched directly — registration is ABN pull from the Australian Business Register (5-7 business days for a fresh ABN) plus a business profile (summary, keywords, categories). No mention of referees, references, or prior-contract proof anywhere in the FAQ. | Fetched `gateway.icn.org.au/faq` directly, 2026-09-02. |
| 1 (softest, tied) | **QLD Supplier Portal (VendorPanel Marketplace)** | **None found.** Registration steps fetched directly: choose categories, register, verify email, complete basic business info/service regions. No reference, referee, or trading-history requirement anywhere on the page. | Fetched `supply.qld.gov.au` directly, 2026-09-02. |
| 3 | **NSW ICT Services Scheme (SCM0020), Registered tier** | **Hard requirement, confirmed**: two (2) referee reports per nominated high-level category, no new-entrant waiver (Q3), eligibility of referee unstated (Q1/Q2). | Scheme Rules §8.1, fetched and full-text-searched directly, 2026-09-02. |
| Unknown | **Digital Marketplace / BuyICT (federal)** | **Could not verify this cycle.** `buyict.gov.au` is a ServiceNow-hosted portal; every URL tried returned only a login-page shell with no eligibility content visible to an unauthenticated fetch. Genuinely blocked, not assumed easy or hard — matches the same login-gated pattern `AU_PANEL_CHECKLIST.md` found for other federal/state procurement sites. | Fetched `buyict.gov.au/sp` and a KB-article URL directly — both returned only login-page markup. |
| Unknown | **QLD Government Arrangements Directory (QGAD)**, and whether a security/pentest panel already exists there | **Could not verify this cycle.** `qgad.epw.qld.gov.au` returned DNS failure on one path and 403 on a related `desbt.qld.gov.au` path. Same named blocking unknown `AU_PANEL_CHECKLIST.md` already flagged (§ "Whether a security/pentest panel already exists on the QLD Arrangements Directory — not checked this cycle") — still not checked. | Attempted fetch, both failed. |

**Ranked recommendation: attack ICN Gateway and the QLD Supplier Portal
first** — both are directly confirmed, this cycle, to have zero
reference/referee gate of any kind. NSW ICT Services Scheme, despite
being the best-shaped opportunity in every other respect (per
`AU_PANEL_CHECKLIST.md`), is the **hardest** of the three routes this
research could actually verify, specifically because of the two-referee
rule.

## Q6 — Any AU panel that explicitly welcomes sole traders with no track record?

**This specific question could not be searched this cycle** — the
session's WebSearch budget was exhausted (200/200 calls used, spent
across this and prior tasks in the same session) partway through this
research, before a targeted query for "explicitly welcomes new/sole
trader/no track record" schemes could be run. This is a named, honest
gap, not a fabricated "no."

What the fetches that *did* succeed already show, functionally: **ICN
Gateway and the QLD Supplier Portal both welcome a business with zero
referees or trading history today** — not because either publishes a
banner saying "sole traders welcome," but because neither imposes a
reference gate at all, which has the same practical effect for this
operator. Recorded as the honest answer available this cycle; a genuine
"explicitly says so" search is the correct next step (raise
`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` or run in a fresh session).

---

## The fastest legitimate way to generate two genuine referees

Only mechanisms that would be **true** referee relationships — nothing
invented, nothing arranged to look like something it isn't.

1. **One paid small engagement, real and billed.** A short, real
   penetration test or security review for any small business/local
   company willing to pay even a modest fixed fee (a few hundred to low
   thousand dollars — this is what NSW's own analogous referee template
   asks for: an "indicative fee for service," dates, and a description
   of what was delivered). This produces a referee who can honestly
   answer every field on the form (timeliness, quality, communication,
   value). This is the single fastest route to a fully unambiguous
   referee, because it removes the entire Q1/Q2 uncertainty — a paying
   client is accepted under any plausible reading of the silent Rules.

2. **A documented pro-bono security review for a local business,
   charity, or non-profit, with a written attestation.** Genuinely
   free, genuinely delivered, with a real scope document, a real
   findings report, and a real signed/emailed acknowledgement from the
   recipient describing what was done and how it went. This is truthful
   — it is not "arranged to look like a client," it *is* real work for
   a real beneficiary, disclosed as unpaid. Whether NSW accepts an
   unpaid engagement is the open question from Q1/Q2 — ask
   `ICTServices@customerservice.nsw.gov.au` before relying on this as
   one of the two, in parallel with doing the work (the work itself has
   value regardless of the answer).

3. **A responsible-disclosure report, acknowledged in writing by the
   receiving organisation.** If the operator finds and responsibly
   reports a genuine security vulnerability to any Australian business
   or open-source project with a disclosure/bug-bounty process, and the
   organisation replies in writing (even a short thank-you/acknowledgement
   email) confirming the report was real, valid, and received — that
   written acknowledgement is truthful evidence of security capability
   from an independent third party. It is a weaker fit for a NSW
   "referee report" (the report format assumes an *engagement*, not a
   single disclosure), but it is honest evidence that could support a
   private application narrative or an ICN Gateway profile even if NSW
   ultimately wants something closer to a client engagement.

4. **Open-source security contributions**, cited as capability evidence
   in the Company Capacity and Capability document (already a required
   §8.1 field, separate from the referee reports) rather than forced
   into the referee-report format — a maintainer's written acknowledgment
   of a merged security-relevant PR or advisory is real, truthful,
   citable evidence, just not necessarily a "referee report" in the
   NSW form's specific sense.

**Recommended order, this week**: do (1) — one small real paid
engagement — as the fastest unambiguous path to referee #1; do (2) in
parallel as referee #2 candidate while confirming via email whether NSW
will accept it; email `ICTServices@customerservice.nsw.gov.au` today
with the Q1/Q2 eligibility question so the answer is in hand before
either engagement finishes. Register on ICN Gateway and QLD Supplier
Portal in the meantime — both are reference-free today and can absorb
whatever capability evidence exists right now, unblocked.

## Named blocking unknowns (not fabricated, explicitly open)

- The actual K03 referee-report form's fields, recency window, and any
  eligibility instructions — only visible after Supplier Hub login;
  the public `SCM5841` template URL returns a CloudFront 403.
- Whether NSW will accept an unpaid/pro-bono engagement as a valid
  referee — the Rules are silent, not permissive or prohibitive; needs
  a direct answer from `ICTServices@customerservice.nsw.gov.au`.
- Exact mechanics of re-submitting after a referee-driven rejection —
  a review path exists in writing, but "can I just reapply immediately"
  is not spelled out.
- BuyICT/Digital Marketplace's actual reference requirement — the whole
  site is login-gated to an unauthenticated fetch; genuinely
  unconfirmed, not assumed either way.
- Whether a cyber/security panel already exists on the QLD Arrangements
  Directory (QGAD) — still not checked, same standing gap
  `AU_PANEL_CHECKLIST.md` already named.
- Q6 (explicit "welcomes sole traders with no track record" language on
  any AU panel) — not searched this cycle, WebSearch budget exhausted.
