# Bug bounty execution plan — Australian sole trader

Written 2026-09-02. Builds directly on `SOLO_REVENUE_ROUTES.md`, which
established: Intigriti public programs (Adobe $75–$15,000, NVIDIA
$150–$15,000, Coveo $100–$5,500, three retail programs $10–$8,500),
Adobe's 1 September 2026 migration to Intigriti, and the payment-gate
finding (ID/KYC + tax form, sole trader explicitly supported on
Intigriti and HackerOne). None of that is re-derived here. This file is
the execution layer: how to actually register, where to point effort,
what the honest odds are, and where the legal line sits.

Operator profile assumed throughout: solo, Australia, ABN held, no
security certification, no professional indemnity insurance, no
corporate entity, no prior bug bounty track record/reputation.

---

## 1. Signup mechanics

### Intigriti

**Registration.** Create an account at `login.intigriti.com/account/register`
or via `www.intigriti.com` → Sign in → enter email → activate via the
emailed link → set up 2FA → land on the researcher dashboard
([Creating an Intigriti account](https://kb.intigriti.com/en/articles/5378975-creating-an-intigriti-account),
[Platform access](https://kb.intigriti.com/en/articles/6908887-platform-access)).
Advice from Intigriti's own docs: don't use your real name as username —
it's shown to program owners in submissions.

**Identity verification.** Required "for KYC purposes and legal
tax/bookkeeping compliance"
([ID Verification Process](https://kb.intigriti.com/en/articles/5378971-id-verification-process)).
Flow: complete profile → "Request ID check" → choose document type and
issuing country → photograph the ID (front/back) → wait for the result.
**Maximum three verification attempts.** A passport or Australian
driver's licence should work as the document (exact accepted document
list is inside the verification flow itself, not published on the help
page — UNKNOWN beyond "government-issued ID, photographed").

**Sole trader status, quoted directly**
([Payouts](https://kb.intigriti.com/en/articles/13653510-payouts)): "a
researcher with a sole trader/proprietorship as a natural person is
taxable through their personal taxes." Two ways to declare payouts: file
your own invoice, or let Intigriti auto-generate one via self-billing
per payout. Intigriti is legally required to report payouts under
**Belgian VAT reporting** regardless of the researcher's own country.
Nothing in the public docs requires an ABN or company registration to
receive payment as an individual — the ABN is relevant to Australian tax
obligations, not to Intigriti's own onboarding gate.

**Payout methods** — five options
([Payout methods](https://kb.intigriti.com/en/articles/3379502-payout-methods)):
- **Wire transfer** — "shortest possible delay"; Intigriti covers its
  own exchange costs but states explicitly: **"We're not able to cover
  transaction and exchange fees that might be charged by your local
  bank."**
- **PayPal** — usable, but **"the currency exchange rate of PayPal can
  be expensive"** — match currency where possible.
- **Payoneer** — **"no additional fees will be charged."**
- **UPI** — India only, not applicable.
- **Invoice** — only for VAT-registered independents (EU VAT scheme, 21%
  VAT, Belgian companies only) — not applicable to an Australian ABN
  holder directly.
- Payments process in the program's default currency, falling back to
  the account's bank currency if unsupported.

Minimum payout threshold: **not stated in the public help articles** —
UNKNOWN, check in-dashboard.

**Practical order of operations:** register → verify email/2FA →
complete profile → run ID check *before* your first submission (payouts
error out if the researcher isn't ID-checked — confirmed by
[Payout lifecycle](https://kb.intigriti.com/en/articles/3379564-payout-lifecycle)) →
set payout method → then submit.

### HackerOne

**Registration.** Standard account creation; no company required.

**Identity verification + tax form + payment method — all three are
required before any payout is released**
([Tax Forms](https://docs.hackerone.com/en/articles/8395744-tax-forms)):
"To receive any kind of monetary award, your account must have a
completed and valid tax form, an approved identity verification, and a
selected payment method." **Tax forms need to be renewed every three
years.**

**ID verification is handled by Veriff, confirmed directly from
HackerOne's own docs**
([ID Verification](https://docs.hackerone.com/en/articles/8399430-id-verification)):
done from the ID Verification section of the profile, consent required,
then redirected to Veriff. Accepted documents: **"passport, ID card,
residence permit, or driver's license"** (country-dependent); may
require a live selfie; **must be completed by the person named on the
tax documentation — no third-party completion.** Verification status is
sent separately, **"usually within three business days,"** and is
**valid 12 months** before it needs renewing. You're only eligible to
start ID verification once you've submitted at least one report or
received a reward — so on HackerOne the ID check happens *after* your
first report, not before, unlike Intigriti.

**Tax form for an Australian individual.** The form selection branches
on "U.S. citizen or U.S. person" vs. non-US, and individual vs.
business/entity — for a non-US individual this is the **W-8BEN**
pathway (the bare label "W-8BEN" was not found stated verbatim on this
specific page in the sections retrieved, but the branching structure
plus Bugcrowd's parallel, explicitly-labelled non-US-individual W-8BEN
requirement below make this the correct, standard IRS-driven form —
treat as SUPPORTED_INTERPRETATION, not a direct HackerOne quote).

**Payment.** Exact methods, minimum thresholds and fee schedule were
**not retrievable from the public help-centre pages** on this pass
(`docs.hackerone.com/en/articles/8395787-external-payments` and
`.../8395720-payment-preferences` did not yield specifics) — UNKNOWN,
confirm inside the dashboard before relying on it. HackerOne's blog
references a "Faster and Better: New Bank Transfer Payment" feature,
indicating bank transfer exists and was recently improved, but no fee
number is confirmed.

### Bugcrowd

**Registration.** No company or business registration required —
"Anyone can sign up to be a researcher on Bugcrowd by creating an
account," individuals participate directly
([Becoming a Researcher](https://docs.bugcrowd.com/researchers/onboarding/becoming-a-researcher/)).
Onboarding: set password → confirm email → set up at least one 2FA
method.

**Tax forms — explicitly three-way split, filed digitally in-platform
(a pre-filled PDF upload is not accepted)**
([non-US individual tax form](https://docs.bugcrowd.com/researchers/payments/setting-up-payment-methods/submitting-tax-form-for-non-us-person-individual/)):
- US person → **W-9**
- **Non-US person, individual → W-8BEN** (this is the Australian sole
  trader's form, filed as an individual, not as a company)
- Non-US person, corporation → W-8BEN-E (not applicable unless the
  operator later incorporates)

**Payment methods, quoted directly:** **"Bugcrowd offers Bank Transfer
and PayPal payment methods. Bitcoin is available for select programs."**
**Fees, quoted directly: "Bugcrowd covers any fees from our account to
the payment provider, but any additional fees are not covered."** Direct
bank transfer is recommended in Bugcrowd's own docs as providing "a
faster transfer timeline and lower conversion rates" than the
alternatives — i.e. your bank's receiving fee is still on you, same
pattern as Intigriti's wire transfer.

### YesWeHack

**KYC/payment provider is MangoPay** (a third party), not YesWeHack
itself — "KYC... a protection process against money laundering & fraud
attempts, used by YesWeHack's Payment Service Provider (MangoPay)"
([KYC verifications & SCA](https://helpcenter.yeswehack.io/en/articles/376519-kyc-verifications-strong-customer-authentication-sca)).
KYC (including Strong Customer Authentication — phone number + PIN,
i.e. MFA on the payment account specifically) is **required to submit
reports and be invited to private programs**, not just to withdraw.
Registration itself: open a Hunter account, complete profile
(skills/experience), accept the Code of Conduct; KYC must complete
before live report submission or private invites.

**Payment.** Rewards are credited to an e-wallet; withdraw via a bank
account "associated with his/her name," or via TransferWise/Payoneer for
certain currencies. **MangoPay does not auto-convert currencies** —
bounties transfer in € or $. **Fees, quoted directly: "YesWeHack does
not take any commission on rewards nor on withdrawals."** The
beneficiary bank may still charge its own wire fee. International
transfers can take up to **15 business days**.

**Tax identification.** A TIN is stated as **"mandatory to authorize a
withdrawal"** for "European private individual hunters" specifically —
whether a non-EU TIN (e.g. an Australian TFN) is accepted the same way
is **not stated** in the public help article. Treat as UNKNOWN, not as
confirmed-absent — do not assume no TIN is needed just because the page
only speaks to European hunters. **YesWeHack generates an invoice for
the hunter**, described as "mandatory to use the platform and submit
reports" — closer to Intigriti's invoice model than HackerOne/Bugcrowd's
US-tax-form model. Given this genuine ambiguity, **YesWeHack is the
lowest-priority of the four platforms for this operator** until the
AU-specific tax mechanics are confirmed directly with their support —
not excluded, just sequenced last.

### Signup order recommendation

1. **Intigriti first** — Adobe/NVIDIA access, clearest sole-trader path,
   ID check front-loaded so it's done before it blocks a payout.
2. **HackerOne second** — largest program catalogue, W-8BEN filed once
   good faith exists a report is coming (ID check only unlocks after a
   first submission anyway, so there's no reason to front-load it).
3. **Bugcrowd third** — Australian-founded, historically stronger local
   corporate coverage (Canva, NAB, Seek — see `SOLO_REVENUE_ROUTES.md`),
   same W-8BEN-individual pattern as HackerOne.
4. **YesWeHack last** — hold until the TIN/invoice mechanics for a
   non-EU sole trader are confirmed; don't let uncertainty block the
   other three.

---

## 2. Scope analysis — Adobe and NVIDIA Public

### Adobe Public (Intigriti)

**The full in-scope/out-of-scope asset list is behind Intigriti's
program-detail login wall** — confirmed directly: fetching
`app.intigriti.com/programs/adobe/adobe/detail` unauthenticated returns
"You actually don't have access to this page." This is genuinely not
publicly readable pre-signup; it is not a research gap that a different
search would have closed.

What **is** publicly confirmed, from
[Adobe's own migration post](https://blog.adobe.com/security/a-new-home-for-the-adobe-bug-bounty-program):
- Go-live on Intigriti: **1 September 2026**. Account setup deadline
  quoted as **31 August 2026** for uninterrupted participation.
- Every new report from 1 September onward must go through Intigriti —
  no parallel HackerOne submission path for new reports.
- Reports filed before the cutoff continue through Adobe's existing
  triage and honor originally-communicated rewards — i.e. the old
  HackerOne program's backlog isn't being reset, only new intake.
- The post references program coverage extending into **AI security
  research** as part of the relaunch, without giving a specific AI asset
  list in the public text retrieved.
- From Adobe's *prior* HackerOne-era policy (may or may not carry over
  verbatim to the Intigriti scope — flagged as historical, not confirmed
  current): **Self-XSS was explicitly excluded** — "for XSS issues to be
  valid they must be exploitable via reflection," i.e. not merely
  something a user pastes into their own console.

**Action required before Adobe work starts:** log into the Intigriti
dashboard once registered and read the actual scope document — this
plan cannot substitute for that, and no report should be filed against
an assumed scope. This is the single most important unresolved item in
this whole plan.

### NVIDIA Public (Intigriti)

Scope **was** publicly readable via direct fetch of
`app.intigriti.com/programs/nvidia/nvidiapublicbugbounty/detail` — this
program's detail page did not gate the way Adobe's did (may reflect
different program visibility settings, may change). Captured 2026-09-02:

**In scope, by product and tier** (tier affects reward multiplier, see
below):

| Product | Tier 1 (highest payout) | Tier 2 | Tier 3 |
|---|---|---|---|
| Container Toolkit | New CDI-based architecture | All other Container Toolkit assets | — |
| CUDA Toolkit | libNVVM API, Nsight Systems, NVIDIA Nsight Developer Tools, NVRTC library | CUDA Libraries, NVCC, nvJitLink APIs | CUDA Runtime APIs, CUDA Driver APIs |

**Explicitly out of scope / excluded:**

*Container Toolkit:*
- Annotation-driven CDI device injection behaviours (working as
  intended)
- Findings that require the attacker to already hold the privilege
  being escalated to
- A container intentionally granted host GPU visibility behaving as
  granted
- Functional gaps with no security impact
- Unreleased code
- Memory-safety defects with no demonstrated impact (i.e. a crash alone
  isn't enough — need to show exploitability)
- Purely theoretical findings

*CUDA Toolkit:*
- Null pointer issues
- Compiler/Object Tools vulnerabilities
- Theoretical issues without a realistic exploit scenario
- DoS/DDoS
- Zero-days reported within 14 days of a patch's public release are
  "usually not eligible for a bounty" — i.e. don't race a patch
  announcement expecting a payout
- Reports claiming an outdated software version without a working PoC

**Reward table** (CVSS-style score bands × tier):

| Severity band (score) | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Low (0.1–3.9) | $300 | $250 | $150 |
| Medium (4.0–6.9) | $2,000 | $1,500 | $750 |
| High (7.0–8.9) | $4,000 | $3,000 | $1,250 |
| Critical (9.0–9.4) | $15,000 | $10,000 | $5,000 |
| Exceptional (9.5–10.0) | $15,000 | $10,000 | $5,000 |

**Requirements that shape where to spend effort:**
- "Always assume local access is required when evaluating
  vulnerabilities" — i.e. NVIDIA scores as if CVSS Attack Vector =
  Local by default. This program is fundamentally about **local
  privilege escalation**, not remote pre-auth exploitation — a very
  different skillset/target profile than a typical web bug bounty.
- Findings that impact end-users are valued over developer-only-impact
  findings.
- Must demonstrate actual code execution at a higher privilege level —
  a crash/DoS is explicitly not enough.
- As of 1 July 2025, DLL hijacking was reclassified down to Tier 3
  (lower payout band) — a signal the easy/well-known DLL-hijack pattern
  is now considered a "known technique," not a novel finding.
- Intigriti account required to submit (standard).

**Implication for effort allocation:** NVIDIA Public rewards **local
exploitation depth in CUDA/Container Toolkit internals** — this suits
someone with systems/reverse-engineering background more than a
generalist web pentester. Adobe's actual scope is unknown pending
login, but Adobe's historical HackerOne-era profile (large web/cloud
product surface — Experience Cloud, Creative Cloud web endpoints, etc.)
is the more web-application-friendly of the two, consistent with
`SOLO_REVENUE_ROUTES.md`'s framing of Adobe as the timing-edge target.
**Read the actual Adobe scope on signup before committing time** — this
recommendation is provisional on that unknown.

---

## 3. Newcomer economics — the honest numbers

This section exists because the plan is a financial decision, not a
motivational one. The evidence, not the aspiration.

**Confirmed, primary-source statistics:**

- **HackerOne 2018 Hacker Report** (survey of ~1,700 hackers,
  [Infosecurity Magazine coverage](https://www.infosecurity-magazine.com/news/bughunting-hackers-earn-top-dollar/)):
  top **1.1%** of hackers earn over **$350,000/year**; top **3%** earn
  more than **$100,000/year**; roughly **12%** earn $20,000+/year; **25%**
  rely on bounties for ≥50% of annual income, **13.7%** for 90–100%. Top
  earners average "2.7x the median software engineer salary" in their
  home country (16x in India). This report does not state a total
  registered-hacker denominator or a time-to-first-bounty figure.
- **Income concentration**
  ([Communications of the ACM, citing HackerOne data](https://cacm.acm.org/careers/247693-this-is-how-much-top-hackers-are-earning-from-bug-bounties/fulltext)):
  **"The top 1% on HackerOne earn more than the bottom 90% combined."**
  Nine individual hackers have earned $1M+ lifetime; 200+ have earned
  $100,000+; roughly 9,000 have earned "at least something" — but the
  total registered-hacker denominator behind that 9,000 figure is
  UNKNOWN in every source checked, so the fraction who've earned nothing
  cannot be computed from this figure alone.
- **HackerOne 2023 milestone**
  ([press release](https://www.hackerone.com/press-release/hackers-surpass-300-million-all-time-earnings-hackerone-platform)):
  community earnings surpassed $300M all-time by 2023-10-26; 30 hackers
  have earned $1M+ lifetime.
- **HackerOne 2026**
  ([BleepingComputer](https://www.bleepingcomputer.com/news/security/hackerone-paid-81-million-in-bug-bounties-over-the-past-year/)):
  **$81 million** paid over the most recent 12 months, with the **top
  100 researchers collectively earning $31.8 million of that** — roughly
  39% of a year's total payouts going to 100 people, against a
  researcher population numbering in the hundreds of thousands. This is
  a power-law distribution, not a normal one; average payout figures
  (e.g. "$X per active program per year") describe program spend, not
  individual researcher take-home, and should not be read as a
  per-hunter expectation.
- **Immunefi** (Web3/smart-contract bounties, a different niche): median
  confirmed payout ≈$2,000, average ≈$52,800 — the same skew shape,
  cited only to show the pattern is consistent across platforms, not
  that it applies directly to web/software bounties.

**Lower-confidence, secondary-source figures — labelled as such, not
platform-published:**

- An aggregator (bug-bounties.as93.net, citing HackerOne/Bugcrowd reports
  and researcher surveys without per-stat source URLs): roughly **40% of
  researchers who submit at least one report never get a single
  bounty**; among *active* hunters, an estimated 35–45% earn $0/year,
  20–25% earn $1–$1,000/year, 15–20% earn $1,000–$10,000/year, and ~20%
  combined earn $10,000+/year. Duplicate/rejection rates of **50–80% for
  newcomers** and 20–40% even for experienced hunters are cited from a
  GitHub researcher note (bl4de/research) — also secondary, not a
  platform-published figure. Treat all of these as
  SUPPORTED_INTERPRETATION at best, not verified fact.
- Bugcrowd's "Inside the Mind of a Hacker 2026" survey (2,000+ hackers):
  92% under 34, 74% cite financial motivation as their top driver,
  critical-vulnerability payouts up 32% YoY — no newcomer-specific
  income-timeline breakout was retrievable from the report on this pass.

**What is genuinely UNKNOWN, not estimated:** no platform publishes an
official average/median **time-to-first-bounty** figure for a brand-new
researcher. The only adjacent "24 hours" statistic found (HackerOne 2019:
77% of *programs* receive their first valid report within 24 hours of
launch) measures program-side speed, not individual newcomer success,
and must not be conflated with it.

**AI-assisted submission volume is actively degrading the newcomer
experience further in 2026, not improving it:** HackerOne reports 1,121
programs now include AI in scope (+270% YoY) and autonomous AI agents
have submitted 560+ valid reports; separately, practitioner reports
describe AI-agent-driven submission floods where roughly half of a batch
of AI-found bugs were duplicates, adding triage noise that slows
*everyone's* response time.

**The honest bottom line:** the primary-source evidence is heavily
skewed toward describing the top of the distribution (platforms publish
"hackers earn millions" headlines, not "median new hacker earns $X in
month one"). What primary data does support is that earnings are
extremely concentrated — combined with the widely-corroborated (though
secondary) 50–80% newcomer duplicate rate on mature public programs, the
honest conclusion is: **a new researcher on a mature, heavily-tested
public program (Adobe, NVIDIA pre-migration) should expect a real,
non-trivial probability of earning nothing for an extended period, and
no platform publishes a number contradicting that.** Treat the first
3–6 months on any given program as unpaid reconnaissance and
skill-building, not income. This is consistent with, not contradicting,
the recommendation to start now — the Adobe migration window is a real,
time-bound reduction in competition (see next section), but "less
competition than usual" does not mean "fast payout for a first-time
hunter." Budget accordingly: this should be a side channel run in
parallel with other income, not a primary plan for near-term cash flow.

---

## 4. Where a newcomer's odds are structurally better

Ranked by currency of the evidence (most time-sensitive first):

1. **Adobe's Intigriti migration (1 September 2026) — already
   established in `SOLO_REVENUE_ROUTES.md`, not re-derived.** Confirmed
   independently via Intigriti's own Bug Bytes #239 newsletter (August
   2026): "Intigriti has been named the new provider for Adobe's Bug
   Bounty Program, effective September 1, 2026"
   ([Bug Bytes #239](https://www.intigriti.com/researchers/blog/bug-bytes/intigriti-bug-bytes-239-august-2026)).
   This remains the single strongest, most current example: a mature,
   well-known target whose duplicate-report history is stranded on the
   old platform. Window is weeks, not months, per the source file's own
   framing.
2. **NVIDIA's bounty program itself is comparatively young** — Intigriti
   and NVIDIA's partnership was announced **18 July 2025**
   ([Intigriti press release](https://www.intigriti.com/blog/business-insights/intigriti-teams-with-nvidia-to-launch-bug-bounty-vulnerability-disclosure-program),
   corroborated by
   [Channel Post MEA](https://channelpostmea.com/2025/07/18/intigriti-and-nvidia-partner-to-launch-bug-bounty-and-vulnerability-disclosure-program/)).
   As of this writing the program is roughly 14 months old — young
   relative to Adobe or Google-scale programs that have run for a
   decade, though no longer "brand new." The scope's specific
   local-privilege-escalation focus (§2 above) also structurally narrows
   the competing researcher pool to people willing to do systems-level
   work rather than generic web scanning, which is a smaller crowd than
   a typical web bounty draws.
3. **U.S. federal-agency programs are actively expanding onto Bugcrowd
   through 2026 — a lower-prestige, less-contested category.** Bugcrowd
   achieved **FedRAMP Moderate Authorization, sponsored by CISA,
   announced 2026-03-03**
   ([press release](https://www.bugcrowd.com/press-release/bugcrowd-achieves-fedramp-moderate-authorization/)),
   and announced a **Carahsoft public-sector reseller partnership on
   2026-04-08**
   ([press release](https://www.bugcrowd.com/press-release/bugcrowd-and-carahsoft-partner-to-bring-fedramp-authorized-proactive-security-and-testing-solutions-to-the-public-sector/)).
   A **CMS (Centers for Medicare & Medicaid Services) Public Bug Bounty
   Program** page exists on Bugcrowd (`bugcrowd.com/engagements/cms-bbpublic`)
   but its exact public-launch date could not be confirmed — flag as
   APPROXIMATE (late 2025–2026), not a verified date. Government/federal
   targets historically draw a smaller researcher pool than glamour
   consumer-brand targets (lower headline prestige, less social-media
   attention) — this is a PLAUSIBLE_HYPOTHESIS from program-count trend
   and general industry pattern, not a measured duplicate-rate
   statistic. **Action: check Bugcrowd's live program list for newly
   listed federal/government engagements at signup time.**
4. **Intigriti's own program directory is a live discovery surface, not
   a fixed list.** The directory (`intigriti.com/researchers/bug-bounty-programs`)
   tags some listings "New" — e.g. **Nederlandse Loterij (Dutch
   Lottery)**, newly listed, but confirmed as a **VDP, not a paid
   bounty** (no monetary reward stated) — note only as an example of the
   "New" tag mechanic, not an income opportunity. **Challenge 0826**, a
   recurring monthly CTF-style Intigriti program also tagged "New," has
   an UNKNOWN payout status — worth checking live, not assumed to pay.
   **Action: check the live directory at signup time for any program
   launched in the prior 4–8 weeks** — a freshly-listed program, by the
   same logic as the Adobe migration, has the least accumulated
   duplicate history. No specific newly-launched *paying* program beyond
   Adobe/NVIDIA was confirmed with a launch date inside the last 8 weeks
   as of 2026-09-02 — this is a standing search habit to build into the
   routine, not a one-time finding.
5. **VDP-to-bounty conversions** are a known industry pattern (a company
   runs a free VDP, proves out its process, then converts to paid) but
   **no specific current example with a confirmed date was found** on
   Intigriti, HackerOne, Bugcrowd, or YesWeHack in this research pass —
   recorded as UNKNOWN rather than fabricated. Searches for HackerOne or
   YesWeHack new-program items returned only platform *feature* launches
   (e.g. "H1 Validation"), not genuine newly-opened paying programs with
   verifiable dates. Worth periodically re-checking each platform's own
   "new programs" feed, not worth inventing a candidate for.

---

## 5. Free tooling

Every tool below is verified to exist and be free/open-source as of this
research pass — nothing invented.

| Category | Tool | What it does | Source |
|---|---|---|---|
| Proxy/interception | **Burp Suite Community Edition** | Manual traffic interception/testing (Repeater, Decoder, Sequencer, Comparer); no automated Intruder/scanner (that's Pro-only) | [portswigger.net/burp/communitydownload](https://portswigger.net/burp/communitydownload) |
| Scope discipline | **Intigriti Quick Scope (IQS)** | Free Burp extension that auto-applies a program's in-scope/out-of-scope rules directly inside Burp — directly useful for staying inside Adobe/NVIDIA scope without manual cross-checking every request | [Intigriti's announcement](https://www.intigriti.com/blog/news/introducing-intigriti-quick-scope-iqs-burpsuite-extension) |
| Scope discipline | **[bbscope](https://github.com/sw33tLie/bbscope)** | Free CLI that aggregates in-scope assets across HackerOne, Bugcrowd, Intigriti, YesWeHack and Immunefi — useful for the "check what's newly in scope" habit from §4 | github.com/sw33tLie/bbscope |
| Subdomain enum (passive) | **[subfinder](https://github.com/projectdiscovery/subfinder)** | Fast passive subdomain discovery from public sources (ProjectDiscovery) | github.com/projectdiscovery/subfinder |
| Subdomain enum (passive+active) | **[OWASP Amass](https://github.com/OWASP/Amass)** | In-depth attack-surface mapping, DNS, passive+active enumeration; official OWASP project, Apache 2.0 | owasp.org/www-project-amass |
| HTTP probing | **[httpx](https://github.com/projectdiscovery/httpx)** | Fast probing of live hosts (status, title, server headers) | github.com/projectdiscovery/httpx |
| Content discovery | **[ffuf](https://github.com/ffuf/ffuf)** | Fast web fuzzer (directories, parameters, vhosts) | github.com/ffuf/ffuf |
| Vuln scanning (template-based) | **[nuclei](https://github.com/projectdiscovery/nuclei)** | Template-driven scanning for known vulnerability/misconfiguration patterns, low false positives | github.com/projectdiscovery/nuclei |

Not independently re-verified against an official source this pass
(name-checked in general research only): **gobuster** (directory/DNS
brute-forcing), **assetfinder**, **Nikto**, **sqlmap** — all are
well-known real OSS tools, but confirm the exact repo/license before
relying on the claim in this plan; do not treat their inclusion here as
independently source-checked the way the table above is.

All of these are CLI/local tools with no paid tier required for the
functionality needed here. Nothing on this list needs a subscription to
be useful at a solo researcher's scale.

---

## 6. The legal line

**Authorised testing is defined entirely by program scope — nothing
else.** Per Intigriti's own community guidance: "Testing out of scope
assets without explicit permission may expose researchers to legal
complaints... only test what they are authorised to test"
([Hacking with permission](https://www.intigriti.com/blog/business-insights/hacking-with-permission-the-rules-that-make-it-ethical)).
Intigriti's Researcher Terms describe program conditions as "minimally
describ[ing] the scope of the Program (target Asset, prohibited
actions, etc.)," and note that where possible assets are listed as
specific domains/URLs/endpoints rather than broad wildcards specifically
to prevent scope misunderstandings
([Program details](https://kb.intigriti.com/en/articles/6899431-program-details)).
Intigriti's terms state explicitly: **"Testing out of scope assets
without explicit permission from the company may expose researchers to
legal complaints, as ethical hacking without permission from the owner
is illegal, even with the best intentions in mind"**
([Researcher Terms & Conditions](https://kb.intigriti.com/en/articles/5466165-researcher-terms-conditions)).
Programs "agree to provide commercially reasonable safe harbor and will
not initiate a lawsuit or law enforcement investigations against
researchers who follow the Rules of Engagement and conduct research
within the bounds of Ethical Hacking" — conditional on the researcher
acting with integrity, reporting responsibly, protecting information
encountered, actively avoiding disruption or damage, and only testing
what they are authorised to test.

**Safe harbour is conditional, not blanket.** HackerOne's Gold Standard
Safe Harbor (GSSH) defines protected conduct as "accessing a computer
solely for purposes of good-faith testing, investigation, and/or
correction of a security flaw or vulnerability, where such activity is
carried out in a manner designed to avoid any harm to individuals or the
public"
([Gold Standard Safe Harbor Statement](https://docs.hackerone.com/en/articles/8494525-gold-standard-safe-harbor-statement)).
Committing organisations state they "will not bring legal action against
you or report you, including for bypassing technological measures" when
research is compliant, and "will take steps to make known that you
conducted Good Faith Security Research if someone else brings legal
action" — but **"organizations are not able to authorize security
research on third-party infrastructure"**, so safe harbour never extends
past what the program owner actually controls. HackerOne's separate
Safe Harbor FAQ states plainly: **"Adopting a Safe Harbor does not
change the program scopes. Scope definitions remain based on what
assets the program explicitly includes"** and **"Security research not
conducted in good faith is not covered by safe harbor... research
conducted for the purpose of extortion is not in good faith"**
([Safe Harbor Overview & FAQ](https://docs.hackerone.com/en/articles/8494502-safe-harbor-overview-faq)).
Bugcrowd's own framing states that safe-harbor language exists
specifically to give "specific authorization, with clear scope, around
anti-hacking laws such as the Computer Fraud and Abuse Act (CFAA) or the
Digital Millennium Copyright Act (DMCA)"
([Bugcrowd guest post](https://www.bugcrowd.com/blog/guest-post-standardizing-legal-safe-harbor-for-security-research/))
— i.e. the entire point of a safe-harbor clause is to pre-authorise
conduct that would otherwise be a CFAA-class offence in the US. None of
the platform pages checked frame this in Australian statutory terms.

**What this means operationally, stated unambiguously:**
- **Testing anything outside a program's declared scope is not
  authorised, regardless of intent** — good intentions do not convert
  unauthorised access into legal cover. This applies even to assets
  that look like they obviously belong to the same company (a
  subdomain, a related product) if it isn't explicitly listed in-scope.
- **Safe harbour only protects behaviour inside the declared rules of
  engagement, and never extends to infrastructure the program owner
  doesn't control** — it is not a general licence to probe a company
  because it happens to run a bug bounty program elsewhere.
- **Disruptive testing voids protection even inside scope** — DoS-style
  testing, data exfiltration beyond proof-of-concept, and social
  engineering against employees are commonly prohibited "prohibited
  actions" under program conditions even when the underlying asset is
  in scope (see NVIDIA's explicit DoS/DDoS exclusion in §2, and
  Intigriti's general "actively avoid causing any disruption or damage"
  language above). HackerOne's GSSH itself instructs researchers to
  "contact us for clarification before engaging in conduct that you
  think may be inconsistent with Good Faith Security Research" — the
  platform-wide statement does not itemise every prohibited action;
  check each individual program's own rules page.
- **The Australian legal backdrop, stated honestly as inference, not
  quoted legal advice:** the applicable unauthorised-access law is
  **Criminal Code Act 1995 (Cth) Part 10.7, Division 477** — s477.1
  criminalises unauthorised access, modification or impairment of data,
  with aggravated versions carrying 5+ years where intent is to commit a
  further serious offence. **No platform or legal-commentary source
  found in this research explicitly maps bug-bounty safe harbour to
  Division 477** — this is a genuine sourcing gap, not an oversight. The
  honest, inferred position: authorisation under a program's published
  scope is what removes the "unauthorised" element of a Division 477
  offence — access is authorised because the asset owner consented via
  that scope. Testing outside it removes the consent basis entirely, and
  Division 477 exposure is real and unmitigated by any platform's safe
  harbour, since (per HackerOne's own words) no program "is able to
  authorize security research on third-party infrastructure." Mark this
  paragraph UNKNOWN/inferred — it is this researcher's own reasoning
  from primary sources, not independently confirmed legal advice; a
  genuinely ambiguous scope question should go to the program's own
  contact channel, not be resolved by guessing.
- **Practical discipline:** before touching any target, read that
  specific program's scope page in full (not this plan's summary, not
  memory from a similar program), use a scope-checking tool (Intigriti
  Quick Scope, or `bbscope` for a fast cross-platform sanity check)
  before firing any request, and stop immediately and re-check if a
  finding leads somewhere that looks like it might be a different
  asset than the one being tested.

This is the one part of this plan with zero tolerance for
approximation: a correct technical finding on an out-of-scope asset is
not a bounty — it is a potential offence.

---

## Summary — the executable sequence

1. Register on Intigriti first (§1); complete Onfido ID check
   immediately, before any submission.
2. Log in and read Adobe's actual current scope page — the real gap
   this plan could not close remotely (§2). Cross-check with Intigriti
   Quick Scope before testing anything.
3. In parallel, review NVIDIA's scope (already captured in full above)
   and decide whether local-privilege-escalation work matches the
   operator's actual skill profile — if not, weight effort toward Adobe
   once its scope is known.
4. Register on HackerOne and Bugcrowd (§1) to keep a wider net open; file
   tax forms (W-8BEN, individual) once a first report is imminent, not
   before — no need to front-load paperwork that isn't yet blocking
   anything.
5. Set a 3–6 month expectation of zero-to-low income while building
   target-specific methodology (§3) — do not treat this as the primary
   income plan during that window.
6. Build the standing habit of checking Intigriti's live program
   directory and Bug Bytes digest every few weeks for freshly-launched
   programs (§4) — the Adobe-style timing edge is a repeatable pattern,
   not a one-off.
7. Every single test action starts with reading that program's current
   scope page — no exceptions, no assumptions carried over from a
   similar program (§6).
