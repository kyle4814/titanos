# DEALS_SELLABLE_ASSETS.md — What Here Is Worth Money, To Whom

Compiled 2026-09-03. Scope: the repository's own code, tests, and
derived knowledge as sellable assets to a THIRD-PARTY BUYER — distinct
from `DEALS_PRODUCTS.md`/`DEALS_SELLING_KIT.md`, which price the
operator's own personal labour (pentesting, policy packs, training).
This file does not duplicate those. Method: read `BUILD_REPORT.md` in
every subsystem, `README.md`, `CLAUDE.md`'s own gate audit,
`experiments/EXP-001/FINDINGS.md`, `foundation/qualification.py` in
full, and `RESOLVED_TARGETS.md`/`RESOLVED_TARGETS_2.md` (the actual
procurement runs). No web search was performed this session — every
competitor/price claim below is either quoted from a source already
fetched and cited elsewhere in this repo, or marked UNKNOWN. Nothing
below is invented.

---

## 1. What is genuinely novel here

Sceptical answer: **one piece of internal scaffolding is arguably
sellable, one piece of applied output is genuinely sellable, and most
of the rest solves a problem this project has that other people don't
have.**

**Not sellable — internal scaffolding, however well-built:**
`kpm/` (claim classification), `firewall/`, `taal/`, `magl/`,
`narrative/`, `foundation/hells_gate.py`, `flow_switch.py`,
`crystal.py`, `sigil.py`. These are genuinely interesting engineering —
forbidden state transitions, two-point enforcement, evidence-gated
promotion — but `CLAUDE.md`'s own gate audit states it plainly:
*"Exactly one [gate] is load-bearing on a real action... The rest...
have no production caller."* A gate nothing calls is not a product; it
is a proof-of-concept for a governance pattern only this project needs,
because only this project has the specific problem of an AI agent
overwriting its own doctrine. `EXP-001` reinforces this from the other
direction: the one module that WAS tested against 28 real documents
(`firewall/gate.py`) was found to grant runtime authority on an
unverified, caller-declared boolean — a real defect, in the one place
closest to being a real product. A capability that only makes sense
guarding this specific codebase's own build discipline is not sellable
software; publishing the write-up of the failure mode itself might be
(see §3).

**Genuinely novel and solves a problem other people have — narrowly:**
The procurement pipeline (`foundation/mouth_ted.py`,
`mouth_find_a_tender_uk.py`, `mouth_gets_nz.py`, `mouth_etenders_ie.py`,
`eligibility.py`, `qualification.py`). This reads five real government
tender feeds and turns TED's structured eForms selection-criterion
codes into a plain-English "can this named operator actually bid"
verdict, with the notice's own quoted clause attached to every
verdict — never a keyword-matched guess. `qualification.py`'s own
docstring records a real bug it was built to fix: the module once
returned `QUALIFIED` for a solo operator against a EUR 14M Helsinki
notice because the disqualifying turnover requirement lived only in
free text TED doesn't code, and it now refuses to clear anything the
codes can't positively resolve (`INSUFFICIENT_DATA`, not `QUALIFIED`,
is the honest default). That refusal-to-guess discipline is the actual
product, not the fetchers — fetchers exist commercially already (see
§2). Whether it's differentiated enough to sell is a separate
question (§3/§5).

**Genuinely novel, arguably a research finding rather than a product:**
The knowledge extracted by running the pipeline against real notices —
see §4. This is the strongest single candidate in the whole repository.

**Everything else** — the doctrine files, the four-agent
Alpha/Beta/Gamma/Delta ritual, the sigil/tier system, the 24-archive
corpus — is process documentation for how this repository builds
itself. It is not a product. Nobody outside this project has the
problem "how do I stop my AI agent from re-deriving the same doctrine
nine times in one session," so there is no external buyer for it, and
this file will not pretend otherwise.

---

## 2. Who would pay for the procurement pipeline

**What it actually does, verified, not inferred from module names:**
fetches TED (EU, ~397,000 open notices, CC BY 4.0, no key), UK
Contracts Finder, UK Find a Tender (OCDS, OGL v3.0, no key), NZ GETS,
and Ireland eTenders; extracts real published selection criteria where
TED's structured codes carry them; and — for the operator's own real
profile — has been run against a real, resolved set of notices with a
real result: **every single notice found and resolved so far
(Bradford MDC, NHS England RM3764, RTÉ Ireland 25P041, EU DG DIGIT
773405-2024, ECHA Helsinki 244223-2024) came back CANNOT APPLY or
DISQUALIFIED.** The pipeline has never yet found a notice the operator
running it can bid on. That is a finding about the tool's honesty, not
a defect — but it directly bears on §3/§5 below.

**Who already sells adjacent things.** This repository's own research
(`DEALS_PRODUCTS.md`, `DEALS_LIVE_CONTRACTS.md`, `DEALS_RECURRING.md`)
did not fetch or verify any tender-alert-service or bid-consultancy
pricing — none is quoted anywhere in this repository with a live
source. I did not run a web search this session either. So, honestly:

- **Tender-alert/notification subscription services** (the market
  category — e.g. commercial UK/EU services that email matching
  notices for a monthly fee) is a real, established market category.
  UNKNOWN: current pricing, named vendors, or market share — not
  verified this session, not asserted here.
- **Bid-writing/bid-management consultancies** (the category — firms
  that write the actual tender response for a fee or success
  commission) is likewise a real, established category. UNKNOWN:
  pricing.
- **Procurement data/market-intelligence platforms** (the category —
  services that aggregate and analyse public-sector spend data) is a
  real category. UNKNOWN: pricing.

**Where this pipeline might sit relative to them, reasoned not
sourced:** alert services answer "does a notice matching my keywords
exist"; bid consultancies answer "help me write the response"; this
pipeline answers a narrower, more mechanical question neither of those
two categories is built around — "given this notice's own *published,
structured* selection criteria, does this specific operator's declared
profile clear the bar, clause by clause, before either of us spends a
day on it." That is a genuine, plausible gap: a screening step that
sits *before* a bid consultancy engagement, saving the wasted labour of
writing a response to a notice a supplier was disqualified from at the
first eligibility line. **This is a plausible gap, not a confirmed
one** — no evidence exists in this repository that any bid consultancy
or SME supplier has ever asked for this, and the pipeline's own
five-for-five DISQUALIFIED track record on the one real profile it has
been run against is itself a small, honest, single-instance sample —
not proof of general usefulness to anyone else.

**Verdict on this question:** the closest real buyer category is
**small/medium suppliers who bid EU public-sector tenders repeatedly**
(not the operator's own current profile, which is disqualified from
every real notice found) and **bid consultancies who screen tender flow
for multiple SME clients**. Both are plausible, neither is confirmed —
no lead, conversation, or expression of interest exists anywhere in
this repository's evidence base.

---

## 3. Is any of it sellable as a product

Realistic about what a solo operator can build, host, and support —
against the operator's own documented profile (`DEALS_PRODUCTS.md`:
solo, Cairns QLD, no certs, no corporate references, strong build
speed, currently zero revenue, zero users):

| Form | Verdict | Why |
|---|---|---|
| Hosted SaaS (subscribe, get matched+qualified notices) | **NOT REALISTIC NOW** | Every "ledger"/store in this repo that would need to survive a restart is explicitly in-memory only (`CLAUDE.md`'s own durability caveat: `crystal.py`, `reality_yield_ledger.py`, `admission.py`, `firewall/quarantine.py`, `kpm/promotion/state_machine.py`, `narrative_atom_store.py` — none survive ordinary process exit). Standing up a real multi-tenant hosted service on top of that would require building persistence, auth, billing, and uptime support this codebase does not have and a solo operator with no track record has no evidenced capacity to run reliably. |
| Paid API (submit a notice + profile, get a qualification verdict) | **PLAUSIBLE, SMALLEST VIABLE FORM** | `qualification.py` is a pure function — no network I/O, no gate required, already tested. Wrapping it in a thin paid endpoint is the smallest real product surface here. Still needs: a durable store (see above), a real customer, and honest labelling that most verdicts will land on `INSUFFICIENT_DATA`/`INFO`, not a clean answer — sell it as "reads the notice faster and more honestly than a human skim," not as "tells you whether to bid." |
| One-off dataset (e.g. "every EU security-procurement notice's selection criteria, structured") | **PLAUSIBLE, LOWEST EFFORT** | The mouths already fetch and structure this; a static export sold once (or per quarter) to a bid consultancy avoids the hosting/support burden entirely. Real limits: TED's own coverage of criteria in codes vs. free text is incomplete (`qualification.py`'s own documented defect against ECHA Helsinki) — the dataset would need to be sold with that limitation stated up front, not discovered by the buyer later. |
| Consulting artefact (the Irish-tender pattern analysis, as a report) | **SELLABLE, HIGHEST CONFIDENCE** | See §4 — this is knowledge, not code, and it is the one asset here closest to something a buyer would recognise as valuable on first read. |
| Selling the codebase/architecture itself (licence, acquire, white-label) | **NOT REALISTIC** | Zero users, zero revenue, unsigned release, `README.md`'s own honesty table: *"Used by anyone: No commercial outcome has ever been observed."* Nobody acquires unproven infrastructure with no customer, however well-tested. |

---

## 4. Is the CODE sellable, or is the KNOWLEDGE

**The knowledge, plainly.** The five Irish tender documents this
repository actually read produced a specific, checkable, valuable
finding a supplier could not get from a keyword search: EU public
security-services procurement in this sample carried Employer's
Liability up to **EUR 13,000,000** (RTÉ 25P041), turnover floors from
**EUR 350,000/yr × 3 years** (RTÉ) up to **average EUR 1,000,000/yr ×
2 years plus five EUR 100,000+ reference contracts** (ECHA Helsinki),
and — the pattern worth naming — **every notice in the sample carried a
reliance/consortium clause**, meaning a supplier who fails one bar
alone is not automatically excluded if they can bring in a partner who
covers it. That last fact is exactly the kind of thing a solo/SME
supplier does not learn from the notice text alone unless someone
reads five real notices closely and compares them — which this
pipeline did, and which is genuinely more useful to another small
supplier than the code that produced it, because:

- The **code** is a general-purpose fetcher+classifier with an honest
  "I don't know" default — useful, but structurally similar to what a
  competent contractor could build from TED/OCDS's own public API
  documentation in a comparable timeframe. Its differentiator is
  discipline (refuses to guess), not a unique data source or algorithm.
- The **knowledge** — the specific EUR thresholds, the specific clause
  pattern, the specific "all five carried a reliance clause" finding —
  cost real reading time to produce and is immediately actionable by
  any other small supplier evaluating whether to bid EU security
  contracts, without them needing to run any code at all. It is also
  the kind of finding that ages: thresholds change per notice and per
  year, so a one-off report is a snapshot, not a subscription — which
  argues for selling it as a **paid briefing/report product**, not a
  live feed (that would require the durable, maintained pipeline this
  repo doesn't yet have, see §3).

**Honest caveat on the knowledge itself:** five documents from four EU
public bodies is a small, non-random sample (whatever notices happened
to be live and readable when this repo went looking), not a
market survey. Selling it as "the EU security-tender market requires
X" would overstate it. Selling it as "here is what five real, current
EU security-services notices actually required, with the clause quoted
so you can verify it yourself" is honest and still valuable — the
value is in doing the reading, not in a claimed sample size it doesn't
have.

---

## 5. What it would take to sell any of this

**For the knowledge (§4 — highest-confidence sellable item):**
- Packaging: a short paid report/briefing — "What EU public-sector
  security-procurement tenders actually require: five real notices,
  quoted clauses, the reliance-clause pattern" — sold once, not
  subscribed to. Low effort: the underlying reading is already done.
- Hosting: none required — a PDF/document sale.
- Support burden: near zero — answer clarifying questions, no ongoing
  service commitment.
- What a first customer needs to see: the quoted clauses themselves
  (already have them, verbatim, in `RESOLVED_TARGETS.md`/
  `RESOLVED_TARGETS_2.md`), and an honest statement of sample size (5
  notices, 4 bodies) so the buyer isn't misled about scope.
- Real gap before selling: **zero identified buyer.** No bid
  consultancy, SME supplier, or tender-alert service has been
  contacted. This is a build-then-sell asset only in the sense that
  the reading is done — nobody has been asked if they'd pay for it.

**For the qualification API (§3 — plausible, smallest viable code
product):**
- Packaging: thin HTTP wrapper around `qualification.assess()`, with
  the existing disclaimer text (`_DISCLAIMER` in `qualification.py`)
  surfaced to the buyer verbatim — the module already refuses to
  overclaim; the product wrapper must not undo that by marketing it as
  more certain than it is.
- Hosting: needs a real persistence layer this repo doesn't have today
  (every relevant store is in-memory-only per `CLAUDE.md`'s durability
  caveat) — this is the single largest build gap before this is
  sellable, not a documentation gap.
- Support burden: moderate — buyers will ask "why did this come back
  INSUFFICIENT_DATA" often, since that is the module's honest default
  outcome on most real notices tested so far, not the exception.
- What a first customer needs to see: a working demo against a real,
  current notice they recognise, and honest disclosure that most
  verdicts will not be a clean yes/no.
- Real gap before selling: same as above — zero identified buyer, plus
  a genuine engineering gap (durable storage, hosting, billing) that
  does not currently exist anywhere in this codebase.

**For everything else in §1 (the internal scaffolding):** not worth
packaging for sale. The honest recommendation is not to spend further
build time making `kpm`/`firewall`/`taal`/`magl` "product-ready" —
`CLAUDE.md`'s own gate audit already establishes they have no
production caller even inside this repository; polishing unused gates
for an external buyer who has never asked for them would be exactly
the "empty theater" this repository's own doctrine warns against
building.

---

## BOTTOM LINE

**The knowledge is sellable. The code is a well-built research tool,
not yet a product, and the doctrine/governance layer is not sellable at
all — it solves a problem only this project has.** The single highest-
confidence, lowest-effort sellable item in this entire repository is
the five-notice EU security-procurement briefing (§4) — the reading is
already done, the packaging cost is near zero, and the only missing
piece is a buyer, which nobody has looked for yet. The qualification
API is the second-best candidate but requires real infrastructure
(persistence, hosting) this repo does not currently have before it
could be sold as a running service rather than a demo. Nothing here
should be represented to a buyer as more finished, more validated, or
more in-demand than the evidence above actually supports — this
repository's own doctrine ("reality must pay," "a claim of future value
is not present value") applies to selling it exactly as much as it
applies to building it.
