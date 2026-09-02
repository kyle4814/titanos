# Global vulnerability markets — the no-company/no-licence/no-insurance/no-references lane

Written 2026-09-03. Builds on `DEALS_BOUNTY_TARGETS.md`, `BOUNTY_STARTING_POSITION.md`,
and `PRIZE_MARKETS.md` — the Ant Group (zero reports), Tencent (15 reports),
Coveo-suspended, NVIDIA-96-days-old, and ZDI/Pwn2Own-Berlin-vs-Ireland
findings are **not re-derived here**. This file maps the wider world those
three did not cover: regional platforms, vendor-direct programs, open-source
bounties, paid government VDPs, and academic/research bounties.

**Method.** Every fact below is a direct quote or close paraphrase from a
program's own published page, fetched read-only with this tool's default,
unmodified User-Agent. No account was created anywhere. No target was
tested, scanned, probed, or sent a crafted request. Where a fetch failed
(JS-rendered shell, 404, DNS failure, connection reset) that is recorded
honestly as **UNKNOWN / UNREACHABLE**, not guessed around. HackerOne's own
program pages are, as `DEALS_BOUNTY_TARGETS.md` §8 already established,
unreachable without executing JavaScript — every HackerOne-hosted program
below (GitLab, AWS, Shopify, DoD, GitHub, many others) inherits that same
blind spot; what's recorded for those comes from the vendor's *own* page
linking to HackerOne, not from HackerOne itself.

---

## 1. The direct answer — pays for Low, ranked by contestedness

| Program | Runs on | Pays for Low? | Low amount | AU individual eligible? | Least-contested signal |
|---|---|---|---|---|---|
| **Ant Group SRC** (carried from `DEALS_BOUNTY_TARGETS.md`) | YesWeHack | Yes | $10 | Yes | **0 reports** — best in either sweep |
| **Tencent** (carried) | YesWeHack | Yes | $20–30 | Yes (KYC, 18+) | 15 reports on a massive surface |
| HackenProof: Zest Protocol | HackenProof | UNKNOWN — not fetched per-program | — | Yes, global | **9 reports, 6 members** — smallest ratio found this pass |
| HackenProof: ZetaChain | HackenProof | UNKNOWN | — | Yes, global | 21 reports, 19 members |
| HackenProof: RISC Zero | HackenProof | UNKNOWN | — | Yes, global | 24 reports, 11 members |
| Meta (Facebook/Instagram/WhatsApp) | Direct (bugbounty.meta.com) | **Yes — $500 minimum bounty stated** | $500 | Not stated; no exclusion found | Huge surface, huge crowd — not under-contested, but confirmed Low-paying floor |
| Apple Security Bounty | Direct | **No for classic Low/Medium** — lowest listed tier is $5,000 (domain takeover) / $10,000 (WebContent code exec); the whole table is exploit-chain-severity, no CVSS-Low tier exists | — | Not stated in fetched pages | Not a first-payout program for a newcomer — table starts where most programs' Critical tier ends |
| Google VRP | Direct (bughunters.google.com) | **UNKNOWN — page is JS-rendered, unreachable this pass** | — | UNKNOWN | UNKNOWN |
| Microsoft MSRC | Direct | UNKNOWN — fetched overview page shows ceilings only ($100k cloud / $250k endpoint / $100k Zero Day Quest), no floor/severity table visible | — | UNKNOWN | UNKNOWN |
| Mozilla (Client + Web bounty) | Direct | UNKNOWN — floor not on the fetched overview page | — | **Yes, explicitly** — only Cuba/Iran/N.Korea/Crimea/Sudan/Syria excluded | UNKNOWN contestedness |
| AWS/Amazon | HackerOne (aws_vdp) | **No — unpaid VDP**, and floor is CVSS ≥4.0 (Medium) just to be *in scope* at all — confirmed from AWS's own page | N/A | N/A — not a paid program | N/A |
| GitLab | HackerOne | UNKNOWN — GitLab's own page explicitly asks reporters *not* to request compensation, defers all payout detail to the HackerOne page (unreachable) | UNKNOWN | UNKNOWN | UNKNOWN |
| Shopify, Cloudflare, Atlassian | HackerOne / Bugcrowd | UNKNOWN — direct program pages 404'd or returned nav-only content this pass | UNKNOWN | UNKNOWN | UNKNOWN |
| Singapore GovTech VDP | Direct | **No — explicitly unpaid**, quoted below | N/A | Not excluded, but moot — no cash | N/A |
| UK NCSC VDP | HackerOne-hosted form | UNKNOWN — no payment terms found on the fetched NCSC page; UK government VDPs are conventionally unpaid, **not independently confirmed unpaid here, flagged not assumed** | UNKNOWN | No restriction found | UNKNOWN |
| US DoD VDP | HackerOne | UNKNOWN — HackerOne page unreachable; DoD's VDP is publicly known to be a no-bounty "safe harbor" program (Hall of Fame only), **this specific claim was not independently re-verified live this session** — treat as UNCONFIRMED, not fact | UNKNOWN | UNKNOWN | UNKNOWN |

**Load-bearing finding:** outside the Ant Group / Tencent pair already found,
**no new program in this sweep was confirmed, from its own primary source,
to pay real cash for a genuine Low-severity finding.** Several likely do
(Mozilla, Microsoft, GitLab) but their floor tables sat behind either a
JS-rendered shell or a second linked page this pass didn't reach. Apple and
AWS are the two clearest **negative** results: Apple's whole reward
structure starts above what a newcomer's first finding usually is, and AWS
doesn't pay at all.

---

## 2. Regional and national bounty platforms

### Zerocopter (Netherlands)
- **What it is, quoted:** "the best way to secure the digital world is to
  work with the best hackers in it" — offers recon, pentesting, bug
  bounty, and coordinated vulnerability disclosure as managed services for
  client organisations.
- **Foreign researcher eligibility:** UNKNOWN — page references a "global
  community of vetted ethical hackers" but no explicit country
  restriction or exclusion was found.
- **Pays cash:** Confirmed a pay-per-valid-finding model ("Pay only for
  valid findings") but no amount, currency, or floor was visible on the
  fetched page.
- **Reports-per-program / contestedness:** UNKNOWN — no public program
  list with report counts was reached this pass.
- **KYC/tax:** UNKNOWN.
- URL: https://www.zerocopter.com/

### Yogosha (France/MENA)
- **What it is:** offensive-security platform running the "Yogosha
  Strike Force" (YSF) — a **vetted, gatekept** community, quoted: "Only
  10% of applicants are accepted into the Yogosha Strike Force (YSF)."
  Applicants pass technical and writing assessments, ID verification, and
  sign NDAs before admission.
- **Open to a foreign individual:** Yes, application is open globally, but
  the **10% acceptance rate is itself a real barrier** distinct from every
  other platform in this file — this is the one platform researched where
  the gate is *before* any program access, not after.
- **Pays cash:** "You pay only when a valid vulnerability is submitted" —
  confirmed pay-per-vulnerability model, no amount/floor found.
- **Verdict for a newcomer:** likely the **worst-fit** platform in this
  sweep specifically because the barrier is a competitive vetting process,
  not an open sign-up — the opposite of "no references" the brief is
  optimising for.
- URL: https://yogosha.com/

### Hackrate (Hungary)
- **Fetch failed** — `ECONNRESET` on the plain homepage request, not
  pushed further per the no-probing rule. **UNKNOWN across every
  dimension.** Public general knowledge only (not verified this session):
  Hackrate is a Budapest-based bug bounty/VDP platform serving mostly
  Central-European clients; treat that single sentence as background, not
  as a sourced fact for this file.
- URL: https://hackrate.com/ (unreachable this pass)

### HackenProof (Ukraine-founded, web3/blockchain focus)
- **What it is, quoted:** "leading specialist bug bounty platform for
  crowd-sourced security testing of blockchain protocols and smart
  contracts." 82,000+ registered hackers, $26,000,000+ paid cumulatively.
- **Open to a foreign individual:** Yes — no geographic restriction found;
  registration is at `dashboard.hackenproof.com/register` with no visible
  country gate.
- **Pays cash:** Yes, **in cryptocurrency** (USDC/ETH/native tokens
  depending on program) — this is a genuine KYC/tax difference from every
  fiat-paying platform in this file: crypto payout means no bank-wire KYC
  step at the platform level, but the researcher still carries their own
  jurisdiction's tax obligation on crypto income (an Australian individual
  receiving USDC/ETH bounty income is not exempted from ATO reporting by
  the payment method — general tax-law inference, not sourced to
  HackenProof's page, marked as such).
- **Pays for Low:** UNKNOWN per-program — the platform-wide range
  ($1,000,000 ceilings down to "$2,000–$10,000 lower-tier programs") does
  not resolve a severity floor without reading an individual program page,
  which this pass did not do.
- **Least-contested finding — this is real, structured data, not
  inferred:** three programs with report:member ratios visible on the
  platform's own leaderboard/stats page:
  | Program | Reports | Members |
  |---|---|---|
  | Zest Protocol | 9 | 6 |
  | ZetaChain | 21 | 19 |
  | RISC Zero | 24 | 11 |
  Zest Protocol's 9 reports is the single lowest absolute report count
  found anywhere in this sweep outside Ant Group's zero — worth a direct
  program-page read before Tencent if smart-contract/blockchain skill is
  the operator's actual strength, not web.
- URL: https://hackenproof.com/

### BugBase (India)
- **Fetch failed twice** — both the homepage and `/programs` returned
  only a page title, no body content (JS-rendered shell, same failure
  pattern as HackerOne). **UNKNOWN across every dimension** — not
  fabricated. What can be said from general public knowledge (not
  verified this session, flagged as such): BugBase is a Bangalore-based
  bug bounty and pentest platform; whether it accepts non-Indian
  researchers, pays in INR or USD, and what its KYC/tax process is were
  not established this pass.
- URL: https://bugbase.ai/ (unreachable this pass)

### Bugv (Nepal)
- **What it is, quoted:** "A crowdsourcing cybersecurity platform powered
  by human intelligence where we connect businesses with cyber security
  experts" — company is Bugv Software Technologies Pvt. Ltd., footer
  states "Proudly Made in Nepal."
- **Open to a foreign individual:** Yes, quoted: researcher community
  described as coming "from all around the world."
- **Pays cash:** Confirmed "Pay For Result" / "Rewards for valuable bugs
  discovered" model, but **no amount, currency, or floor found** on the
  fetched page — genuinely UNKNOWN, not zero.
- **Contestedness:** UNKNOWN — no program list with report counts reached.
- URL: https://bugv.io/

### Safe Security, Cyber Army, Cyscope, Zeroday.cz
- **Not independently fetched this pass** — session's WebSearch budget
  was exhausted before these could be queried (200/200 used, mid-sweep;
  WebFetch on direct URLs continued to work and is what the rest of this
  file relies on). **Genuinely unresearched, not silently assumed absent
  or worthless.** Flagged as the clearest next step for a follow-up
  session with search budget restored.

### Intigriti, YesWeHack, Bugcrowd, HackerOne, Open Bug Bounty
- Already fully covered in `DEALS_BOUNTY_TARGETS.md` §§1,6–9 — **not
  re-derived here.** One addition this pass: Intigriti's own researcher
  landing page (`intigriti.com/researchers`) states "400+ active
  programs, 150K+ bounties paid, €50M+ total" but the fetched page
  carried no eligibility, KYC, or tax detail for a non-EU (e.g.
  Australian) researcher — that specific question remains UNKNOWN from
  Intigriti's own marketing page and would need the researcher-facing
  FAQ/terms, not fetched this pass.

---

## 3. Vendor-run programs with no platform intermediary

### Google VRP
- **Fetch blocked both attempts** — `bughunters.google.com/about/rules/...`
  returns only a page title with no body; the site is JS-rendered and not
  readable by this tool without executing JavaScript, the same limitation
  already established for HackerOne. **Genuinely UNKNOWN this pass** —
  payout ranges, Low-severity policy, Australian eligibility, and OSS VRP
  detail could not be confirmed from Google's own primary source. General
  public knowledge (not verified this session): Google's VRP is widely
  known to pay from the low hundreds of dollars up to $151,000+ for the
  most severe Android/Chrome findings, and to accept researchers globally
  with no known country exclusion — **stated here only as background, not
  as a sourced fact for this file's ranking.**
- URL: https://bughunters.google.com/about/rules (unreachable this pass)

### Microsoft MSRC
- **Confirmed from Microsoft's own overview page:** three current
  programs — Cloud Programs (up to $100,000), Endpoint & On-Prem Programs
  (up to $250,000), Zero Day Quest (up to $100,000), overall ceiling
  "$250,000 USD in bug bounty awards."
- **Low severity / floor:** Not stated on the overview page — quoted
  language only says higher-quality/higher-impact reports "qualify for
  higher awards," which does not resolve whether a genuine Low pays at
  all. UNKNOWN, not zero.
- **AU eligibility:** Not addressed on the fetched page — deferred to
  "Microsoft Bounty Terms and Conditions," not itself fetched.
- URL: https://www.microsoft.com/en-us/msrc/bounty

### Apple Security Bounty
- **Confirmed, full table from Apple's own categories page** (this is the
  best-sourced vendor program in this file):

  | Attack class | Target | Reward |
  |---|---|---|
  | Network attack, no interaction | Kernel | $2,000,000 |
  | Network attack, no interaction | User space | $350,000 |
  | Network attack, interaction | Kernel | $1,000,000 |
  | Wireless proximity | Application processor | $1,000,000 |
  | Physical access | Sensitive data | $500,000 |
  | App sandbox escape | Kernel | $500,000 |
  | App sandbox escape | Sensitive data | $100,000 |
  | Browser attack | Kernel | $1,000,000 |
  | Browser attack | WebContent sandbox escape | $300,000 |
  | Browser attack | WebContent code execution | $10,000 |
  | Unauthorized iCloud access | Server-side breach | $1,000,000 |
  | Remote code execution (services) | Command injection/deserialization/XXE | $100,000 |
  | File system/DB access | Unsandboxed XXE, SQLi | $50,000 |
  | Logic flaw | Security control bypass | $50,000 |
  | Client/server code execution | XSS/CSRF/HTML injection | $40,000 |
  | Data exposure | PII access control | $30,000 |
  | Domain takeover | DNS/subdomain takeover | $5,000 |

  Bonus multipliers: beta software +50%, Lockdown Mode bypass +100%, both
  +150%. macOS-specific: Gatekeeper bypass $100k, TCC capture $5–10k,
  sandbox escape $5k.
- **Pays for Low: effectively no.** The **entire table floor is $5,000**
  (a full domain/subdomain takeover) — there is no CVSS-Low tier at all;
  this program is structurally built around exploit chains and severe
  primitives, not the missing-rate-limit/low-impact-IDOR class of finding
  a realistic newcomer produces first. **Explicitly ruled out as a
  first-payout target** on the same logic `BOUNTY_STARTING_POSITION.md`
  already applied to Adobe/NVIDIA, but more severe here — Apple's whole
  table starts above where most other programs' *Critical* tier ends.
- **AU eligibility / KYC:** not found in the fetched categories page,
  deferred to a separate Terms and Conditions page not fetched.
- URL: https://security.apple.com/bounty/categories/

### Meta (Facebook/Instagram/WhatsApp)
- **Confirmed from Meta's own bug bounty page:**
  | Category | Max payout |
  |---|---|
  | Mobile RCE | $300,000 |
  | Account takeover | $130,000 |
  | 2FA bypass | $20,000 |
  | Contact point deanonymisation | $10,000 |
  | Page admin disclosure | $5,000 |
  | **Minimum bounty** | **$500** |
  Hacker Plus programme adds up to 30% bonus on top of any bounty.
- **Pays for Low: yes, confirmed** — the explicit "$500 minimum bounty"
  statement is the clearest floor figure found for any vendor-direct
  program in this sweep.
- **AU eligibility:** not restricted on the fetched page; general
  invitation, no country exclusion visible.
- **Contestedness:** high — Meta is a famous, heavily-tested surface;
  not ranked as under-contested, only confirmed as Low-paying.
- URL: https://bugbounty.meta.com/

### Amazon / AWS
- **Confirmed: unpaid VDP, not a bug bounty**, from AWS's own page. Key
  quotes: submissions via HackerOne (`hackerone.com/aws_vdp`, itself
  unreachable) or email; **"Issues must have a CVSS score of 4.0
  (MEDIUM) or higher"** to be accepted as in-scope at all; must be
  "Customer Impacting"; safe-harbor protection offered but **no
  compensation of any kind mentioned anywhere on the page.**
- **Verdict:** ruled out entirely for a first-payout objective — it does
  not pay, and its own floor (CVSS ≥4.0) is already above what this
  brief defines as a realistic newcomer first finding (Low/Medium).
- URL: https://aws.amazon.com/security/vulnerability-reporting/

### GitHub, GitLab, Atlassian, Cloudflare, Shopify
- **GitLab** — confirmed HackerOne-hosted ("report any security
  vulnerabilities in GitLab itself via our HackerOne bug bounty
  program"), but GitLab's own page explicitly asks reporters "to refrain
  from requesting compensation for reporting vulnerabilities" in the body
  text fetched, then separately points to the HackerOne policy for actual
  rules — an odd, uncomfirmed signal worth flagging rather than resolving:
  **do not assume GitLab is unpaid from this alone**, the HackerOne page
  (unreachable) is the actual authority and may show a standard paid
  bounty table; this is exactly a case where the primary source could not
  be reached and the secondary source reads ambiguous.
- **Atlassian, Cloudflare, Shopify** — all three direct-page fetches
  failed this pass (Atlassian's Bugcrowd page returned nav-only content;
  Cloudflare's and Shopify's direct URLs both 404'd, likely stale paths).
  **Genuinely UNKNOWN**, not fabricated. Public general knowledge (not
  verified this session): all three are known to run paid bounty programs
  (Atlassian and Shopify via HackerOne/Bugcrowd historically, Cloudflare
  via HackerOne) — flagged as background only.
- **GitHub** — not independently fetched this pass; carried forward as
  UNKNOWN.

---

## 4. Open-source and infrastructure bounties

### Internet Bug Bounty (IBB)
- **Fetch blocked** — hosted on HackerOne (`hackerone.com/ibb`), same
  JS-rendered-shell limitation as every other HackerOne page in this
  file. **Genuinely UNKNOWN this pass.** General public knowledge (not
  verified this session): the IBB is run by the OpenSSF/Linux Foundation
  umbrella, pays out of a pooled fund for vulnerabilities in widely-used
  open-source infrastructure (OpenSSL, curl, and similar), and has
  historically paid real cash — flagged as background only, not sourced
  for this file.
- URL: https://hackerone.com/ibb (unreachable this pass)

### OpenSSF Alpha-Omega
- **Confirmed from Alpha-Omega's own homepage:** an OpenSSF initiative,
  "protect society by catalyzing sustainable security improvements
  across open source," annual budget over $7M, works "in partnership
  with maintainers, security researchers, and the global open source
  community."
- **Direct payment to individual researchers: NOT confirmed.** The
  fetched homepage lists a leadership team of program managers affiliated
  with member organisations (AWS, Microsoft, Google) but **does not
  describe an individual bounty or grant application path** — this reads
  structurally more like a funder of maintainer/organisation-level
  security work than a per-bug payer. **This is a real finding, not a
  gap**: Alpha-Omega does not appear to be a bug-bounty-shaped income
  route for a solo individual the way ZDI or a platform program is.
- **Verdict:** not ranked in the "pays for Low" table — no individual
  payout mechanism was found.
- URL: https://alpha-omega.dev/

### Google OSS VRP / patch rewards
- **Fetch failed** — `bughunters.google.com/about/rules/oss` returned
  404. **UNKNOWN this pass**, same JS-rendering/URL-drift problem as the
  main Google VRP page above. Flagged for a follow-up fetch at the
  correct current URL, not fabricated here.

### EU-FOSSA / EU Free and Open Source Software Audit programme
- **Fetch failed** — DNS resolution error on the attempted European
  Commission URL. **UNKNOWN — could not confirm current existence,
  status, or payout structure this pass.** This is a genuine research
  gap, consistent with `PRIZE_MARKETS.md`'s own prior finding that
  European Commission and Australian government sites were frequently
  unreachable in that sweep too. Worth a follow-up with a corrected URL
  (the programme, if still active, would likely now be under the EU's
  "sovereign tech fund"-style initiatives rather than the old EU-FOSSA
  branding, which ran roughly 2017–2019 as a pilot — general knowledge,
  not verified this session).

---

## 5. Government VDPs that pay

- **Singapore GovTech VDP — confirmed unpaid.** Direct quote from
  GovTech's own page: **"GovTech will not in any way... Provide you with
  any cash reward or financial incentive of any kind for the detection
  and/or resolution of the validated vulnerability."** Non-financial
  "recognition" only, at GovTech's sole discretion. Testing/exploitation
  is explicitly prohibited even to confirm a suspected vulnerability
  ("attempts to exploit or test suspected vulnerabilities... are
  prohibited") — this is a pure disclosure channel, not a testing
  ground. **Ruled out entirely for this brief's purpose.**
- **UK NCSC VDP — payment status UNKNOWN, not confirmed either way.**
  Fetched page covers scope (UK government online services, Scottish
  Government services, NCSC's own site) and process (5-working-day
  initial assessment, HackerOne-hosted submission, optional account) but
  **contains no explicit statement about compensation in either
  direction.** No country restriction found. Do not assume unpaid from
  silence — flagged UNKNOWN, follow-up needed on the HackerOne-hosted
  submission page itself (unreachable this pass).
- **US DoD VDP (Hack the Pentagon lineage) — UNKNOWN, not independently
  re-verified.** HackerOne's `deptofdefense` page is unreachable
  (JS-rendered shell, same limitation as every other HackerOne page).
  It is well-established public knowledge that DoD's standing VDP is
  historically unpaid (Hall of Fame recognition, not cash — separate
  from occasional paid live-hacking events like "Hack the Pentagon" or
  "Hack the Air Force" which are time-boxed and invitation- or
  qualification-gated) — **stated here as background only, explicitly
  not verified against DoD's own current page this session.**
- **EU institutions — not independently researched this pass.** Flagged
  as a genuine gap for a follow-up session, same as EU-FOSSA above.

**Net finding for this section: zero government VDPs were confirmed, from
a primary source read this session, to pay cash.** One (Singapore) was
affirmatively confirmed unpaid. This matches the brief's own framing —
"most VDPs do not pay" — and this sweep did not find the exception.

---

## 6. Academic and research bounties

**Not independently researched this pass** — the session's WebSearch
budget was exhausted (200/200) before this category could be queried, and
no stable direct URL for a specific academic/research security-prize
programme was already known to fetch without a search step first. This
is the same honest gap `PRIZE_MARKETS.md` §6 already recorded for its own
sweep ("session's search tool was exhausted before this category could be
covered"). **Flagged as the clearest single next research step**, not
silently skipped or invented.

---

## 7. Least-contested ranking — report-count / attack-surface ratio, not payout size

Ranked by the strongest available *evidence of low competition* found
across both this file and the two prior files, best first:

1. **Ant Group Security Response Center (YesWeHack)** — 0 reports,
   explicit "recruit global talent" language. Carried from
   `DEALS_BOUNTY_TARGETS.md` §6, the strongest single data point in
   either sweep.
2. **Zest Protocol (HackenProof)** — 9 reports, 6 members, against a
   full blockchain protocol's attack surface. New find this pass. Caveat:
   requires blockchain/smart-contract skill, not general web skill, and
   its per-severity payout table was not read this pass — UNKNOWN
   whether it pays for Low.
3. **Tencent (YesWeHack)** — 15 reports against WeChat/QQ/WeChat
   Pay/Tencent Cloud. Carried from `DEALS_BOUNTY_TARGETS.md` §6.
4. **ZetaChain (HackenProof)** — 21 reports, 19 members. Same
   blockchain-skill caveat as Zest Protocol.
5. **RISC Zero (HackenProof)** — 24 reports, 11 members. Same caveat.
6. **Superdrug / AS Watson trio (Intigriti)** — no report-count field
   exists on Intigriti's platform (confirmed absent in
   `DEALS_BOUNTY_TARGETS.md` §1), so this can't be ranked by the same
   metric — carried forward only as the existing narrow-scope,
   real-money argument already made in `BOUNTY_STARTING_POSITION.md`.

**Everything else in this file — Zerocopter, Yogosha, Hackrate, BugBase,
Bugv, Google VRP, Microsoft, Apple, Meta, AWS, GitLab, Atlassian,
Cloudflare, Shopify, every government VDP, Alpha-Omega, IBB, EU-FOSSA —
has no report-count or researcher-density figure available from what was
reachable this session.** Recording that absence honestly is the correct
output here, not filling it with an estimate.

---

## 8. Sources

- https://security.apple.com/bounty/ , https://security.apple.com/bounty/categories/
- https://www.microsoft.com/en-us/msrc/bounty
- https://bugbounty.meta.com/ (redirected from https://www.facebook.com/whitehat)
- https://aws.amazon.com/security/vulnerability-reporting/
- https://about.gitlab.com/security/disclosure/
- https://www.mozilla.org/en-US/security/bug-bounty/
- https://www.zerocopter.com/
- https://yogosha.com/
- https://hackenproof.com/
- https://bugv.io/
- https://www.intigriti.com/researchers
- https://www.ncsc.gov.uk/information/vulnerability-reporting
- https://www.tech.gov.sg/report_vulnerability
- https://alpha-omega.dev/
- Unreachable this pass (recorded, not guessed around):
  https://bughunters.google.com/about/rules (JS-rendered),
  https://bughunters.google.com/about/rules/oss (404),
  https://hackerone.com/ibb , https://hackerone.com/deptofdefense ,
  https://hack.dhs.gov/ (DNS failure),
  https://digit-europa.ec.europa.eu/DIGIT/collections/eu-fossa (DNS failure),
  https://hackrate.com/ (connection reset), https://bugbase.ai/ and
  https://bugbase.ai/programs (JS-rendered shell),
  https://developers.cloudflare.com/support/.../bug-bounty-program/ (404),
  https://www.shopify.com/legal/report-abuse-vulnerability (404),
  https://bugcrowd.com/engagements/atlassian (nav-only content)
- `DEALS_BOUNTY_TARGETS.md`, `BOUNTY_STARTING_POSITION.md`,
  `PRIZE_MARKETS.md` (this repository, reused not re-derived)

## 9. What this file did NOT do

Did not test, scan, probe, or send any crafted request to any target
system. Did not create an account on any platform. Did not spoof a
User-Agent. Did not research or include grey-market/exploit-broker sales.
Did not fabricate a program, payout figure, or eligibility rule — every
UNKNOWN above is a genuine fetch failure or absent detail, not a filled-in
guess.
