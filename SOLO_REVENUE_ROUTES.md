# Paid security work with no certification, insurance, or company

Written 2026-09-02. Every figure here was read off the operator's own
published page on the date shown, not from a summary article. Where a
secondary source and a primary source disagreed, the primary source won
and the disagreement is recorded.

## Why this file exists

Three procurement markets were swept end to end and the result was
negative for a solo operator:

- **Australia** — unreachable without defeating a WAF. Not attempted.
- **New Zealand** — 337 live tenders, zero cyber security work.
- **EU (TED)** — real demand, but TED notice `578580-2026` (degewo AG,
  €691,200) states its bidder conditions as `Ausschlusskriterien`:
  three penetration testers on staff, two corporate references of
  ≥€50,000 each, €3,000,000 liability insurance, CEFR C1 German. That
  shape is not one fussy buyer; above the GPA threshold a public body is
  obliged to ask for something like it.

The operator has: one person, no certifications, no insurance, no
corporate reference history. Public tendering is therefore a **dominated
channel** — more feeds will return more of the same wall.

Bug bounty is the inverse. It pays for **results**, not for paperwork
proving you are likely to produce results.

## Verified live programs — read 2026-09-02

From Intigriti's public program directory. "Public" here means no
invitation, no certification, no company registration.

| Program | Sector | Range |
|---|---|---|
| Adobe Public | Software | **$75 – $15,000** |
| NVIDIA Public | Software | **$150 – $15,000** |
| ICI PARIS XL | Retail | $10 – $8,500 |
| The Perfume Shop | Retail | $10 – $8,500 |
| Marionnaud | Retail | $10 – $8,500 |
| Coveo Public | Software | $100 – $5,500 (2FA required) |
| Daytona | Software | €200 – €3,500 (2FA + application) |

### The timing edge on Adobe

**Adobe's bug bounty moved to Intigriti on 1 September 2026 — yesterday.**
Intigriti was named Adobe's new provider, and from that date every new
report must be submitted on the new platform.

That matters more than the $15,000 ceiling. A migrated program resets
the duplicate landscape: the report history that made every easy finding
a duplicate sits on the *old* platform, and the researcher population
that had been grinding that surface has to re-onboard. A program in its
first weeks on a new platform is the least-crowded a mature target ever
gets. If any single item in this file is time-sensitive, it is this one,
and the window is measured in weeks.

A further seventeen programs on the same page (Dashlane, Grafana Labs,
ESA, SolarWinds, TrueLayer, Wärtsilä, University of Basel, CARIAD and
others) are **VDPs — responsible disclosure, no money**. They are worth
distinguishing sharply: a VDP buys reputation, not income. Do not let a
long program list read as a long list of paying programs.

## What actually gates payment

Not skill credentials. Identity and tax paperwork:

- **Intigriti** — ID verification for KYC, then valid payout details.
  A **sole trader / sole proprietorship is explicitly supported** as a
  natural person, taxed through personal tax. Researchers may invoice;
  if they don't, Intigriti issues a tax sheet under Belgian law.
- **HackerOne** — a valid tax form, identity verification through
  Veriff (valid 12 months, renewed), and a selected payment method.
  Tax forms renew every three years. Names must match across both.

That is the entire barrier. It is an afternoon of admin, not a
qualification, an insurance policy, or a reference history.

## Australian programs

- **Canva** — runs a bug bounty on Bugcrowd.
- **National Australia Bank** — launched via Bugcrowd in 2020, one of
  the first Australian banks to do so.
- **Seek** — on Bugcrowd since 2019; highest reward reported at $10,000.
- **Bugcrowd itself was founded in Sydney in 2012**, which is why
  Australian corporate coverage is unusually good on that platform
  specifically.

**South Australian Government — does NOT pay.** The Department of
Premier and Cabinet announced a paid program in an October 2023 approach
to market, and trade press reported "financial rewards". But the
official `security.sa.gov.au` vulnerability-reporting page, as of March
2026, states the SA Government does **not** provide compensation for
finding vulnerabilities. The announcement and the live policy disagree;
the live policy is the one that pays. Recorded here so nobody chases the
press release.

## The Australian door that is actually open

Three procurement markets were swept and Australia was written off as
unreachable. That was true of AusTender's *tender feed*. It is not true
of Australian government *supplier access*, which is a different thing
and was never tested until now.

### NSW ICT Services Scheme (SCM0020) — always open

Quoted from buy.nsw's own FAQ, read 2026-09-02:

- **Turnover is not an acceptance criterion.** Verbatim: *"No. It is
  requested for informational purposes but does not form part of the
  acceptance criteria."*
- **Registered tier** — *"enter into low-risk contracts valued up to
  $150,000 (excluding GST)"* under simplified terms with *"lower
  insurances, to reduce the cost of doing business with government."*
- **Advanced tier** — contracts over $150,000, *"higher level of
  acceptance requirements."*
- **ABN is the hard requirement.** *"Yes, if they have an Australian
  Business Number (ABN)."* Overseas companies may apply if they obtain
  one.
- **Always open.** New suppliers may register at any time; no deadline.

No certification is named as an acceptance criterion. No corporate
reference history. No staff minimum. Compare that to TED `578580-2026`.

### Queensland — no panel gate at all

QITC has no panel or accreditation gate; contracting is direct,
per-engagement, through QTenders (`qtenders.hpw.qld.gov.au`, robots.txt
fully permissive, but a Blazor WebAssembly SPA whose data API was not
located — a human can browse it, a fetcher currently cannot).

### Victoria — the one with a real wall

The eServices register requires **$5,000,000 public liability
insurance**. That is a genuine barrier and is recorded so it is not
attempted first.

### ICN Gateway

`gateway.icn.org.au` — reachable, free registration, no certification
gate found. This is subcontracting exposure rather than prime panel
membership, which matches the operator's actual position.

### What this changes

The earlier conclusion — "public tendering is a dominated channel" —
was drawn from *tender notices* and is correct about them. It was wrong
as a statement about Australian government work generally. The NSW
registered tier is a $150,000 contracting ceiling reachable with an ABN
and no credentials, in the operator's home country and language, open
today with no closing date to miss.

## Honest limits

This is **results-paid work with no floor.** A month of effort can
return zero. Duplicate reports earn nothing. The public programs listed
above are the most-tested attack surfaces on the internet precisely
because they are open to everyone, so the easy findings are gone.

What it is not: blocked. Unlike every tender in the three markets
swept above, nothing here requires a credential the operator does not
have. The gate is competence and persistence, which is the correct gate.

## Sources

- https://www.intigriti.com/researchers/bug-bounty-programs
- https://www.intigriti.com/blog/news/intigriti-named-new-provider-for-adobes-bug-bounty-program
- https://blog.adobe.com/security/a-new-home-for-the-adobe-bug-bounty-program
- https://app.intigriti.com/programs/nvidia/nvidiapublicbugbounty/detail
- https://kb.intigriti.com/en/articles/13653510-payouts
- https://kb.intigriti.com/en/articles/5378971-id-verification-process
- https://docs.hackerone.com/en/articles/8395744-tax-forms
- https://docs.hackerone.com/en/articles/8395787-external-payments
- https://bugcrowd.com/engagements/canva
- https://www.security.sa.gov.au/cyber-security/report-a-security-vulnerability
- https://www.itnews.com.au/news/sa-gov-to-create-bug-bounty-program-579301
