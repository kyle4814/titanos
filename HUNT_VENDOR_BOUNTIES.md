# Vendor-run bug bounties with no platform intermediary — the "pays for Low" hunt

Written 2026-09-03. Direct follow-on to `GLOBAL_VULN_MARKETS.md` §1/§3/§4 —
those confirmed findings (Meta pays $500 min, DOES pay Low; Apple floor
$5,000, NO Low tier at all; AWS unpaid VDP; Singapore GovTech unpaid,
testing prohibited) are **not re-derived here.** This file is a second
pass at the eighteen programs `GLOBAL_VULN_MARKETS.md` left UNKNOWN,
fetched by direct URL rather than search (session's WebSearch budget was
already exhausted — 200/200 — before this pass started; every result
below came from `WebFetch` against a URL typed directly, no search
engine involved).

**Method, unchanged from the prior file.** Every fact is a direct quote
or close paraphrase from a program's own page. No account created, no
target tested/scanned/probed, no User-Agent spoofed. A failed fetch
(404, JS-rendered shell, timeout, wrong redirect target) is recorded
honestly as UNKNOWN/UNREACHABLE, never guessed around.

---

## 1. The direct answer — pays for Low, ranked by realistic first-payout odds

Ranking rule: a program that structurally cannot pay for Low is ranked
below one that might, regardless of ceiling size — a newcomer's first
real finding is realistically a Low, not a Critical.

| Program | Pays cash direct? | Pays for Low? | Low amount | AU eligible? | Verdict |
|---|---|---|---|---|---|
| **Meta** (carried from `GLOBAL_VULN_MARKETS.md`) | Yes, direct | **Yes — confirmed** | $500 min | Not restricted | Best confirmed first-payout target in either sweep |
| Google VRP | UNKNOWN — still unreachable | UNKNOWN | — | UNKNOWN | Two more direct-URL attempts this pass both hit the same JS-rendered-shell wall; genuinely not resolved |
| **Microsoft MSRC — M365 Bounty Program** | Yes, direct | **No — confirmed negative** | N/A | Not stated on this page | See §2 below — full table read this pass, explicit "$0" for Moderate/Low |
| Mozilla (client bounty) | Yes, direct | **Discretionary only, not a floor** | — | UNKNOWN (page has no country statement) | See §2 — real quote found, resolves the prior UNKNOWN partially |
| Apple (carried) | Yes, direct | **No** — floor is $5,000 | — | UNKNOWN | Ruled out, unchanged |
| AWS (carried) | No — unpaid VDP | N/A | N/A | N/A | Ruled out, unchanged |
| LINE | **No — program suspended** | N/A | N/A | N/A | New negative finding this pass, see §2 |
| GitHub | Yes, direct (via HackerOne submission) | UNKNOWN — only minimums for Critical found ($10k public / $30k private), no severity floor table reached | — | UNKNOWN | Still unresolved |
| GitLab, Atlassian, Cloudflare, Shopify, Zoom, Samsung, Dropbox, Adobe, LINE(pre-suspension detail), Grab, Automattic, Slack | UNKNOWN across the board | UNKNOWN | — | UNKNOWN | Every direct-URL guess 404'd or returned a nav-only/marketing shell this pass — see §3 |
| Internet Bug Bounty | UNKNOWN — no individual-payout mechanism found | UNKNOWN | — | UNKNOWN | `internetbugbounty.org` now redirects to a HackerOne marketing page for "Community Edition" (HackerOne's free-tier product for OSS maintainers), not IBB program terms — see §4 |
| OpenSSF Alpha-Omega | **No individual payout mechanism found** (unchanged from `GLOBAL_VULN_MARKETS.md`) | N/A | N/A | N/A | Attempted follow-up redirect landed on an unrelated third-party blog post, not fetched — see §4 |
| Google OSS VRP | UNKNOWN — every attempted URL 404'd | UNKNOWN | — | UNKNOWN | See §4 |

**Load-bearing finding, restated with this pass's new evidence added:**
still only **Meta, Ant Group, and Tencent** are confirmed, from a
primary source, to pay cash for a genuine Low. This pass adds one
concrete **negative**: Microsoft's M365 Bounty Program explicitly pays
**$0** for Moderate/Low severity — its entire table only activates at
Critical/Important. Mozilla is now better understood as **discretionary,
not floored** — a real Low might get paid, but nothing on Mozilla's own
page promises it, unlike Meta's explicit "$500 minimum." Everything else
targeted this pass (12 of 18 named programs) remained genuinely
UNREACHABLE by direct URL — a real research gap, not a hidden negative.

---

## 2. Confirmed reads this pass

### Microsoft MSRC — M365 Bounty Program
- **URL:** https://www.microsoft.com/en-us/msrc/bounty-microsoft-cloud
- **Confirmed full table** (three vulnerability-class groups, each split
  Critical/Important severity × High/Medium/Low *exploitability* —
  important distinction: this "Low" is a sub-rating of exploitability
  quality *within* an already-Critical-or-Important-severity report, not
  a CVSS-Low severity tier):
  - Deserialization/Code Injection: Critical $15k/$10k/$6k (High/Med/Low
    exploitability), Important $10k/$6k/$4k
  - Auth issues, info disclosure, SQLi/command injection, SSRF, access
    control: Critical $12k/$8k/$4k, Important $6k/$4k/$2k
  - XSS/CSRF/misconfig/cross-origin/input validation: Critical
    $8k/$5k/$2.5k, Important $4k/$2.5k/$1.25k
- **Explicit quote:** "Such vulnerability must be of Critical or
  Important severity as defined by the Microsoft Vulnerability Severity
  Classification for Online Services" — **Moderate and Low severity
  submissions receive $0.** This is the clearest structural negative
  found this pass: like Apple, MSRC's whole reward architecture starts
  above where a newcomer's realistic first finding usually sits, even
  though the ceiling ($250,000 combined across programs, per
  `GLOBAL_VULN_MARKETS.md`) is far below Apple's.
- **AU eligibility / country exclusion:** not stated on this specific
  program page — deferred to Microsoft's general Bounty Terms and
  Conditions, not fetched this pass either.
- **Verdict:** ruled out as a first-payout target on the same logic as
  Apple and AWS — confirmed, not inferred.

### Mozilla — client bug bounty
- **URL:** https://www.mozilla.org/en-US/security/client-bug-bounty/
- **Confirmed table:** Highest Impact up to $20,000 (e.g. sandbox
  escape), Higher Impact $10,000 (UXSS), High Impact $3,000
  (sec-high-rated bugs, GPU memory corruption, info disclosure).
- **Direct quote on Low:** "Typically, the security rating given by the
  Bounty Committee for a bug must be rated a 'sec-high' or
  'sec-critical' in order for it to be eligible for a bounty. In some
  circumstances, bounties may be paid for lower-rated bugs as well."
- **Verdict:** this resolves the prior file's UNKNOWN to **"maybe, at
  the Bounty Committee's discretion — not a stated floor."** Meaningfully
  different from Meta's unconditional $500 minimum: a newcomer cannot
  rely on a Low being paid here, only hope for discretionary
  consideration. Ranked below Meta, above Microsoft/Apple.
- **AU eligibility:** genuinely not on this page — `GLOBAL_VULN_MARKETS.md`'s
  country-exclusion list (Cuba/Iran/N.Korea/Crimea/Sudan/Syria) was
  presumably sourced from Mozilla's separate terms page, not this one;
  not re-verified this pass.
- Web bounty page (https://www.mozilla.org/en-US/security/web-bug-bounty/)
  fetched separately — no table found on that specific page either, it
  points onward to Mozilla's HackerOne listing (unreachable, same
  standing limitation as every HackerOne page in this project).

### LINE — program suspended (new negative finding)
- **URL:** https://bugbounty.linecorp.com/en/
- **Direct quote:** "No reward will be paid under this program for
  reports submitted on or after the suspension date" — **suspended as
  of 2025-12-03.** Reports can still technically be emailed in, but with
  no financial compensation during suspension.
- **Verdict:** ruled out entirely for a first-payout objective for as
  long as the suspension holds — this is a real, dated, sourced
  negative, not an assumption.

### GitHub — partial
- **URL:** https://bounty.github.com/
- **Confirmed:** GitHub runs its own bounty (submissions still routed
  through HackerOne, but the program itself is GitHub-branded/run, not a
  HackerOne-operated third-party program in the Intigriti/Bugcrowd
  sense). Two tiers: public program ($10,000+ for critical) and private
  program ($30,000+ for critical).
- **Not found:** any severity table below Critical, so whether a Low
  pays anything is still genuinely UNKNOWN — the page links onward to
  `/rewards` and `/scope`, neither fetched this pass.

---

## 3. Unreachable this pass — recorded honestly, not guessed around

Every one of these was attempted at a direct, plausible URL (no search
engine used) and failed. Listed with the exact failure so a future
session doesn't repeat the same dead guess:

| Program | URL(s) tried | Failure |
|---|---|---|
| Google VRP | `bughunters.google.com/about/rules/6625378258649088`, `.../6625378258649088/google-and-alphabet-vulnerability-reward-program-vrp-rules` | Page title only, JS-rendered shell — same limitation `GLOBAL_VULN_MARKETS.md` already recorded, confirmed again with a second, more specific URL |
| GitLab | `about.gitlab.com/security/disclosure/` | Confirmed again: page explicitly says "please refrain from requesting compensation for reporting vulnerabilities," defers actual payout table to HackerOne (unreachable) — same as prior file, not a new finding |
| Atlassian | `www.atlassian.com/trust/security/bug-bounty` | 404 |
| Cloudflare | `www.cloudflare.com/vulnerability-disclosure-policy/`, `www.cloudflare.com/disclosure-policy/` | Both 404 |
| Shopify | `shopify.engineering/bug-bounty`, `www.shopify.com/trust/vulnerability-disclosure` | Both 404 |
| Zoom | `explore.zoom.us/en/trust/security/security-bug-bounty/` (redirected to a 404 page), `www.zoom.com/en/trust/security/security-bug-bounty/` | 301 redirect chain ending in Zoom's own 404, then direct guess also 404 |
| Samsung | `security.samsungmobile.com/bugBounty.smsb`, `.../securityReward.smsb` | Both 404 — URL slug guessed wrong twice, correct path not found this pass |
| Dropbox | `www.dropbox.com/security`, `help.dropbox.com/security/bug-bounty-program` | First returned a general trust/pricing page with no bounty content; second 404 |
| Adobe (direct) | `helpx.adobe.com/security/bug-bounty.html` (404), `helpx.adobe.com/security/alertus.html` (timeout) | Neither resolved — genuinely not read this pass, cannot confirm or deny whether Adobe runs a direct (non-Intigriti) program |
| Grab | `engineering.grab.com/grab-bug-bounty-program` | 404 |
| Automattic | `automattic.com/security/` | Confirmed page exists but only says "submit via HackerOne portal" — no table, same shape as GitLab |
| Slack | `slack.com/trust/security/bug-bounty-program` | 404 |
| Yahoo/Paranoids | not attempted this pass | No plausible direct URL was known to try without a search step — genuinely not researched, not silently assumed absent |

---

## 4. Open-source bounty programs — the requested deep dive

This is the section the brief asked for real depth on. Honest result:
**direct-URL research this pass could not get past the same wall found
in `GLOBAL_VULN_MARKETS.md`.** Recorded in full rather than padded.

### Internet Bug Bounty (IBB)
- **`internetbugbounty.org` now 301-redirects to
  `hackerone.com/internet-bug-bounty`.** That page, when fetched, turned
  out to be **HackerOne's own marketing content for "HackerOne Community
  Edition"** — a free vulnerability-coordination *product* HackerOne
  sells to open-source maintainers — not IBB's own program rules,
  scope, or payout table. This is a genuinely new and mildly concerning
  finding: **the IBB's own domain no longer serves IBB-specific
  content**, it serves HackerOne product marketing. Whether the IBB
  program itself still operates, under what name, with what payout
  table, could not be established from this redirect.
- **What is still only general public knowledge, explicitly not
  verified this session, carried forward from the prior file:** the IBB
  is historically associated with the OpenSSF/Linux Foundation umbrella
  and has paid real cash for vulnerabilities in widely-used open-source
  infrastructure (OpenSSL, curl, and similar). **This claim remains
  unconfirmed from any primary source reached in either sweep.**
- **What qualifies, what it pays, how to submit — all three genuinely
  UNKNOWN.** Not fabricated. The honest state of this research question
  after two sweeps is: the historical existence of a program by this
  name is well-known; its current operational status, payout mechanism,
  and submission path are not established from any primary source this
  project has reached.

### OpenSSF Alpha-Omega
- **Unchanged from `GLOBAL_VULN_MARKETS.md`'s finding:** Alpha-Omega
  funds maintainer/organisation-level security work (audits, tooling,
  training) rather than paying individual researchers per-bug. This
  pass attempted one follow-up fetch (`alpha-omega.dev/reports/`) which
  **301-redirected to an unrelated third-party security-news blog post**
  about a different topic ("Akrites Open Source Security Framework") —
  not Alpha-Omega's own content, so it was not fetched or used as a
  source. **This redirect behaviour itself is worth flagging**: either
  the `/reports/` path no longer exists on Alpha-Omega's own site, or
  it was retired and the domain-level redirect rule is stale/broad.
- **Verdict, restated:** still not a bug-bounty-shaped income route for
  a solo individual with no track record. No new evidence changes this.

### Google OSS VRP
- **All three attempted URLs 404'd or hit the same JS-rendered-shell
  wall this pass:** `bughunters.google.com/about/rules/oss` (prior
  file, 404), a Google Security Blog post about the OSS VRP's 2022
  launch (404 this pass — likely a stale/moved URL, the program is now
  three-plus years old and Google's blog URLs are not stable long-term).
- **Genuinely unresolved across two sweeps.** What is general public
  knowledge, not sourced to any primary page reached in either sweep:
  Google's OSS VRP is widely reported (in third-party security-industry
  coverage, not fetched or cited as fact here) to pay for vulnerabilities
  found in Google's own open-source projects and in the OSS supply chain
  Google depends on (build pipelines, CI/CD config, dependencies), with
  reported floors in the low hundreds of dollars — **stated here purely
  as background context for what to search for once this session's
  search budget resets, not as a sourced fact for this file's ranking
  table.**

### Why this section could not go deeper this pass
The brief's own instruction — "read published program pages ONLY," no
testing/probing/account creation — was followed throughout. The genuine
blocker was infrastructure, not effort: this session's WebSearch tool
was exhausted (200/200) before this category could be reached with a
search step to find the *current, correct* URLs, and every guessed
direct URL for these three programs specifically landed on a 404,
redirect-to-unrelated-content, or JS-shell. **This is the single
clearest next step for a follow-up session with search budget
restored** — the same honest gap `GLOBAL_VULN_MARKETS.md` §6 already
recorded for academic bounties, now recorded here for open-source
bounties specifically, which the brief flagged as the highest-priority
under-examined category.

---

## 5. Sources

- https://www.microsoft.com/en-us/msrc/bounty-microsoft-cloud (fetched,
  full table read)
- https://www.mozilla.org/en-US/security/client-bug-bounty/ (fetched,
  table read)
- https://www.mozilla.org/en-US/security/web-bug-bounty/ (fetched, no
  table found)
- https://bugbounty.linecorp.com/en/ (fetched, suspension confirmed)
- https://bounty.github.com/ (fetched, partial)
- https://about.gitlab.com/security/disclosure/ (fetched, confirmed
  same finding as prior file)
- https://automattic.com/security/ (fetched, no table)
- https://www.hackerone.com/internet-bug-bounty (fetched — redirect
  target of internetbugbounty.org, found to be unrelated HackerOne
  product marketing, not IBB's own content)
- Unreachable this pass (404/timeout/JS-shell, recorded not guessed
  around): bughunters.google.com (two URLs), atlassian.com/trust/
  security/bug-bounty, cloudflare.com (two URLs),
  shopify.engineering/bug-bounty + shopify.com/trust/
  vulnerability-disclosure, explore.zoom.us + zoom.com bug-bounty pages,
  security.samsungmobile.com (two URL guesses), dropbox.com/security +
  help.dropbox.com/security/bug-bounty-program, helpx.adobe.com (two
  URLs, one 404 one timeout), engineering.grab.com/grab-bug-bounty-
  program, slack.com/trust/security/bug-bounty-program,
  alpha-omega.dev/reports/ (redirected to unrelated content, not
  followed)
- `GLOBAL_VULN_MARKETS.md` (this repository, reused not re-derived)

## 6. What this file did NOT do

Did not test, scan, probe, or send any crafted request to any target
system. Did not create an account anywhere. Did not spoof a User-Agent.
Did not use WebSearch (budget was exhausted before this pass began —
every URL above was typed directly or reached via a server-issued
redirect, never via a search-engine result). Did not fabricate a
program, payout figure, or eligibility rule — every UNKNOWN above is a
genuine fetch failure, not a filled-in guess. Did not research
grey-market/exploit-broker content.
