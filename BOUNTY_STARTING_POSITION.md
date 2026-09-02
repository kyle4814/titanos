# Starting position — first paying-lane target, read before touching anything

Written 2026-09-02. Builds on `BUG_BOUNTY_PLAN.md` and
`SOLO_REVENUE_ROUTES.md` — signup mechanics, KYC/tax gates, the legal
line, and the newcomer income statistics are not re-derived here. This
file is scope + ranking + tooling + a first week, for the five
accessible Intigriti public programs.

**This is document research only.** Nothing in this file involved
sending a request to Adobe, NVIDIA, ICI PARIS XL, The Perfume Shop,
Marionnaud, or any infrastructure they own. Every quote below came from
reading each program's own published brief page. No account was
created on any platform.

## A methodology caveat that matters more than any single number below

`BUG_BOUNTY_PLAN.md` (written 2026-09-02, same day) recorded that a
direct unauthenticated fetch of Adobe's program page returned "You
actually don't have access to this page" — genuinely login-gated at
that time. Today, an AI-mediated fetch of the same URL, and of NVIDIA's,
and of all three retail programs', returned full scope content without
logging in. Two honest explanations, not resolved here: (1) Adobe's
program is now genuinely public-readable, consistent with the 1
September 2026 Intigriti migration having completed the day before this
was written; (2) the fetch path used here renders or caches differently
than a bare unauthenticated HTTP request and the page is not actually
open to an anonymous visitor. **Treat every quote below as
high-confidence but not final** — re-read each program's live brief
inside the Intigriti dashboard immediately after signup, before
building any methodology or filing any report against it. If a number
here has drifted, the in-dashboard version is the one that governs a
real submission.

---

## 1. Scope, quoted from each program's own brief

### Adobe Public

**In scope** (by tier):
- Tier 1 (AI models, bonus-eligible): "Adobe AI suite including Firefly,
  Photoshop AI Assistant, Lightroom AI, Acrobat AI Assistant, Adobe
  Stock AI Studio, and others"
- Tier 2: mobile apps (Acrobat Reader, Adobe Scan, Lightroom, Photoshop
  Express, Adobe Fresco, Frame.io); web apps `*.acrobat.adobe.com` |
  `stock.adobe.com` | `firefly.adobe.com` | `*.lightroom.adobe.com` |
  `photoshop.adobe.com`
- Tier 2-3: ColdFusion (with/without Administrator), Adobe
  Commerce/Magento, Adobe Learning Manager, Adobe Behance, Adobe
  Express, Adobe Portfolio, Adobe Fonts, Adobe IMS services

**Reward table (CVSS band × tier):**

| Severity | Score | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|---|
| Low | 0.1–3.9 | $150–300 | $100–250 | $75–100 |
| Medium | 4.0–6.9 | $300–1,500 | $250–1,000 | $100–500 |
| High | 7.0–8.9 | $1,500–7,500 | $1,500–5,000 | $500–1,500 |
| Critical | 9.0–9.4 | $7,500–10,000 | $5,000–7,500 | $1,500–3,000 |
| Exceptional | 9.5–10.0 | $10,000–15,000 | $7,500–10,000 | $3,000–5,000 |

**Accepted classes, quoted:** "Remote code execution (RCE),
SQL/command/LDAP injection, Server-Side Request Forgery (SSRF),
Cross-site scripting (XSS), CSRF in privileged contexts, directory
traversal, authentication/session flaws, authorization flaws including
IDOR, account takeover, unauthorized data access, sensitive file
exposure, security misconfiguration, prompt injection with backend
impact, AI-specific vulnerabilities."

**Explicitly excluded, quoted:** "Denial-of-service or resource
consumption testing unless it leads to sensitive memory disclosure";
self-XSS without exploitation affecting other users; "Logout and other
low-severity CSRF"; open redirects with low impact; missing HTTP
security headers; password policy observations; "Username or email
enumeration via login or forgot password error messages"; SSL/TLS
best-practice findings; "Known-vulnerable libraries without proof of
exploitation." AI-specific: "Prompt influence without backend impact";
"Role confusion without unauthorized disclosure of internal system
prompts, policies, secrets, credentials"; "Model response deviation,
hallucination, or safety response variation without security control
bypass." Mobile: "Vulnerabilities in mobile applications relying on
installation of a malicious APK"; "Mobile app submissions requiring
rooted or jailbroken devices." General: social engineering, physical
attacks, unapproved customer environments, assets not explicitly
listed, duplicates.

**Requirements:** testing IP address must be provided, sufficient
reproduction detail, proof of being first reporter, adherence to
product-specific test plans in Adobe's own attached test plan document
— that attachment was not itself retrievable here; read it before
starting.

### NVIDIA Public

Already fully captured in `BUG_BOUNTY_PLAN.md` §2 — re-confirmed
unchanged today. Local-privilege-escalation focus (CVSS Attack
Vector=Local assumed by default), Container Toolkit + CUDA Toolkit
in scope, DLL hijacking downgraded to Tier 3 since 1 July 2025,
DoS/DDoS and null-pointer issues explicitly excluded, reward table
$300–$15,000 across Low→Exceptional × Tier 1–3.

### ICI PARIS XL

**In scope**, by tier:
- Tier 1 (e-commerce core): `www.iciparisxl.nl/.be/.lu`, Android/iOS
  apps, `app.`, `media.`, `api.` subdomains for all three ccTLDs
- Tier 4 (lower priority): `www.iciparisxl.com`, `xlence.iciparisxl.nl`,
  newsletter/folder/edition/wifi-in-store/campaign/service domains
- Tier 5 (wildcards, minimal payout): `*.iciparisxl.lu/.nl/.be`,
  `www.pourvous.nl` and `*.pourvous.nl`

**Focus areas, quoted:** "E-commerce Payment & order flows,
Authorization flaws in API & Microservices, Any e-commerce
functionality which processes customer data." Named critical
scenarios: "Mass customer data exposure: emails, addresses, phone
numbers, order history"; "Zero-click mass customer account takeover";
"Remote Code Execution"; "Unauthorized access to important
infrastructure, databases, or backend systems"; "Checkout/order process
abuse (e.g. free or discounted products)."

**Excluded, quoted:** "Wordpress usernames disclosure, Pre-Auth
Account takeover/OAuth squatting, Self-XSS, verbose messages without
sensitive info, CORS on non-sensitive endpoints, missing cookie
flags/security headers"; "CSRF with no/low impact, clickjacking without
proven impact, CSV injection, sessions not invalidated,
username/email enumeration, email bombing, HTTP request smuggling
without impact, subdomain takeover without actual takeover, arbitrary
file upload without proof." Mobile: "Shared links in clipboard, no
session timeout, absence of certificate pinning, sensitive data in
TLS-protected URLs, lack of obfuscation, path disclosure, lack of
jailbreak detection."

**Reward table:**

| Severity | CVSS | Tier 1 | Tier 2 | Tier 4 | Tier 5 |
|---|---|---|---|---|---|
| Low | 0.1–3.9 | $100–350 | $100–300 | $50–100 | $10–25 |
| Medium | 4.0–6.9 | $350–1,250 | $300–1,000 | $100–500 | $25–50 |
| High | 7.0–8.9 | $1,250–4,000 | $1,000–3,000 | $500–1,000 | $50–100 |
| Critical | 9.0–9.4 | $4,000–7,500 | $3,000–5,000 | $1,000–1,500 | $100–250 |
| Exceptional | 9.5–10.0 | $7,500–8,500 | $5,000–5,500 | $1,500–2,000 | $250–500 |

Validation SLA quoted: Exceptional/Critical within 3 working days,
High within 7, Medium/Low within 15.

### The Perfume Shop

Same reward table, same validation SLA, same "E-commerce Payment &
order flows / Authorization flaws in API & Microservices / any
e-commerce functionality processing customer data" focus language as
ICI PARIS XL — word-for-word close enough to be the same program
template.

**In scope, by tier:** Tier 1 — `www.theperfumeshop.com`,
`app.theperfumeshop.com`, `api.theperfumeshop.com`,
`media.theperfumeshop.com`, Android/iOS apps. Tier 4 —
`campaign.theperfumeshop.com`, `campaigns.theperfumeshop.com`,
`ecom-data.theperfumeshop.com`. Tier 5 — `*.theperfumeshop.com`
wildcard.

**Excluded, quoted, application level:** "Self-XSS (single-user), CORS
on non-sensitive endpoints, missing security headers, CSRF with no/low
impact, rate limit bypasses, CSV injection, username enumeration,
subdomain takeover without actual takeover, blind SSRF without proven
impact." General: "DoS/DDoS, brute force attacks, theoretical issues
without realistic exploits, physical access scenarios, MitM attacks,
zero-days within 14 days of patch release." Mobile: "Lack of
certificate pinning, absence of jailbreak detection, lack of
obfuscation, missing anti-debugging controls, runtime hacking
exploits."

**Operational requirements, quoted:** "Researchers must use
@intigriti.me email addresses" and "Maximum 5 requests/second for
automated testing" — the second is a hard rate-limit rule, relevant to
every tool in §4 below.

### Marionnaud

Same template again, extended across markets. **In scope:** Tier 1 —
`www.marionnaud.fr/.at/.ch/.it` and apps/API/media for those; Tier 2 —
Hungary, Czech Republic, Romania, Slovakia main sites/apps at reduced
payout; Tier 4 — `campaign.marionnaud.*`, `ecom-data.marionnaud.*`,
`extranet.marionnaud.ch`; Tier 5 — wildcard domains across all markets
(`*.marionnaud.fr`, `*.marionnaud.es`, `*.marionnaud.com`, etc.) at
minimal payout.

**Excluded, quoted:** "Wordpress usernames disclosure, Pre-Auth Account
takeover/OAuth squatting, Self-XSS that can't be used to exploit other
users," missing security headers/cookie flags, CORS on non-sensitive
endpoints, CSRF with low impact, username enumeration, banner grabbing,
arbitrary file upload without proof. General: "DoS/DDoS attacks or
brute force attacks, Attacks requiring physical access to a victim's
computer/device, man in the middle or compromised user accounts,"
theoretical issues, zero-days within 14 days of patch. Mobile: "Lack of
jailbreak & root detection, The absence of certificate pinning, Lack of
obfuscation, Lack of binary protection controls."

Same reward table and validation SLA as ICI PARIS XL / The Perfume
Shop.

---

## 2. The AS Watson finding — a real, verified multiplier

**All three retail programs are hosted under the same Intigriti
organisation slug: `app.intigriti.com/programs/aswatson/...`** — ICI
PARIS XL, The Perfume Shop, and Marionnaud are run by the same
corporate submitter, described on the program listing as belonging to
"AS Watson Group" and offering "financial incentives when valid
vulnerabilities are discovered." This is a directly observed fact from
the URL structure and program listing text, not an inference.

**What this changes, concretely:**
- The three briefs are near-word-for-word identical in focus language,
  excluded-vulnerability list, reward table, and tier structure — this
  is not three independently-written policies, it is one policy
  template applied to three brands. A methodology (rate-limit
  discipline, which endpoint classes to prioritise, what "zero-click
  mass account takeover" means for their platform) built for one
  transfers almost directly to the other two.
- **This is a real, legitimate multiplier, not a scope violation, with
  one hard boundary: each brand's domains are separately listed and
  separately scoped.** A finding on `iciparisxl.nl` does not authorise
  touching `marionnaud.fr` — that would be testing an out-of-scope
  asset under a different program and is exactly the "explicit
  permission per asset" rule `BUG_BOUNTY_PLAN.md` §6 already covers.
  What transfers legitimately is the *vulnerability class and
  methodology*, not the authorisation. If the same corporate group runs
  the same e-commerce platform/microservices stack behind all three
  brands (a real possibility given the identical "Authorization flaws
  in API & Microservices in the e-commerce environment" language across
  all three, but not confirmed — mark as PLAUSIBLE_HYPOTHESIS, not
  verified), a bug class found on one brand's checkout flow is a strong
  hint of where to look on the next brand — each still requires its own
  separate testing, separately authorised by that brand's own listed
  in-scope assets.
- Three separately-scoped, separately-payable programs from one
  learning investment is the single strongest reason to start here
  rather than on Adobe or NVIDIA. See ranking below.

---

## 3. Ranking for a newcomer specifically — not by ceiling, by real odds

**1st: ICI PARIS XL / The Perfume Shop / Marionnaud (AS Watson trio) —
start here.**
- Reasoning: `SOLO_REVENUE_ROUTES.md` already flagged these as "far
  less contested" than Adobe/NVIDIA, and the scope confirms why —
  narrow, well-defined e-commerce surface (checkout, auth, customer
  data APIs) rather than a decade-deep sprawling product suite. A
  narrow scope with clear "what we actually want" language (mass data
  exposure, zero-click ATO, checkout abuse) is easier for a newcomer to
  aim at productively than a huge surface where the easy findings are
  long gone. Reward floor is honest ($10) but the ceiling ($8,500) is
  close to Adobe's mid-tier bands, and three separately-payable programs
  exist behind one learning curve (§2). The $100–350 Low band on a
  narrow e-commerce scope is a realistic first target for someone with
  no track record — a missing rate limit or a low-impact IDOR is a
  plausible first find; a Critical RCE on Adobe is not.
- Concrete first move: ICI PARIS XL specifically (listed first
  alphabetically and structurally identical to the other two) — then
  reuse the same methodology against The Perfume Shop and Marionnaud
  once it's been proven against one.

**2nd: NVIDIA Public — only if the operator's actual skill profile is
systems/reverse-engineering, not web.**
- Reasoning: genuinely younger program (partnership announced July
  2025, ~14 months old vs. Adobe's decade-plus history), and its
  local-privilege-escalation focus structurally narrows the competing
  pool to people willing to do systems-level work — a smaller crowd
  than generic web scanning draws. But this is a real skill-fit gate,
  not a free ranking boost: if the operator's actual background is web
  application testing, NVIDIA's local-access CVSS assumption and CUDA
  internals focus make this a poor fit regardless of the lower
  competition, and the honest odds collapse back toward Adobe-level
  difficulty for someone learning CUDA/driver internals from zero
  simultaneously with learning bug bounty methodology.

**3rd: Adobe Public — largest ceiling, largest crowd, real but
short-lived timing edge.**
- Reasoning: the $15,000 ceiling and huge asset list (AI suite, mobile
  apps, ColdFusion, Magento, Learning Manager, Behance, Express,
  Portfolio, Fonts, IMS) is the most attractive-looking number on this
  page, and the migration-reset timing edge from `BUG_BOUNTY_PLAN.md`
  §4 is real. But Adobe is also the program with the deepest prior
  report history (moved from a decade-old HackerOne program, not
  founded fresh) — the duplicate-history reset applies to the
  *platform*, not to the underlying application code, which is the same
  code that's been tested for years. Rank this third for a newcomer
  specifically: worth registering for and watching, not worth spending
  the first week's limited attention on ahead of the AS Watson trio.

**Not ranked — Coveo Public and Daytona:** both require an application
and/or 2FA gate beyond plain registration (per `SOLO_REVENUE_ROUTES.md`)
— not blocking, just an extra step, sequenced after the four above are
underway.

---

## 4. Free toolchain — install commands, verified this pass

All commands below are for Linux/WSL with a working Go toolchain
(`go version` — install via your distro's package manager or
https://go.dev/dl/ if missing; every ProjectDiscovery tool below needs
Go ≥1.24).

| Tool | What it's for | License / maintenance (verified) | Install |
|---|---|---|---|
| **Burp Suite Community Edition** | Manual request interception, Repeater/Decoder/Comparer — the core workbench for reading and replaying requests by hand within the 5 req/s limits these programs set | Free; confirmed on PortSwigger's own download page ("Start your web security testing journey for free"); Linux platform support not itemised on the page fetched — PortSwigger has shipped a Linux `.sh` installer for years, confirm current build at download time | Download the Linux installer from `portswigger.net/burp/communitydownload`, `chmod +x` it, run it |
| **subfinder** | Passive subdomain discovery — maps `*.iciparisxl.*` / `*.theperfumeshop.com` / `*.marionnaud.*` wildcard scope from public sources only, no requests to the target itself | MIT, actively maintained (2,248+ commits, active issues/PRs) | `go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| **httpx** | Fast probing of which discovered hosts are actually live, with status/title/headers — the step after subfinder, before deciding what to manually test | MIT, actively developed (README warns of breaking changes between releases — pin a version rather than always running `@latest` mid-engagement) | `go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| **nuclei** | Template-driven scanning for known misconfigurations/CVEs — useful as a low-noise triage pass, not a substitute for manual testing; must respect the 5 req/s cap these programs state explicitly (`-rate-limit 5`) | MIT, actively maintained (same breaking-changes caveat as httpx — pin versions) | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| **ffuf** | Fast content/parameter/vhost fuzzing | MIT, actively maintained (16.6k stars, active issues/PRs) | `go install github.com/ffuf/ffuf/v2@latest` (Homebrew/Scoop/Winget alternatives exist for other OSes) |
| **bbscope** | Aggregates in-scope assets across HackerOne/Bugcrowd/Intigriti/YesWeHack/Immunefi in one CLI call — the "check what's actually in scope right now" habit `BUG_BOUNTY_PLAN.md` §4 already recommends | Apache-2.0, actively maintained (411+ commits); Docker image also available via GHCR | `go install github.com/sw33tLie/bbscope/v2@latest` |
| **Amass** | Deeper DNS/attack-surface mapping than subfinder alone, passive+active enumeration | Apache 2.0, actively maintained (2,874+ commits) — **note the project moved GitHub orgs, now at `github.com/owasp-amass/amass`, not the old `OWASP/Amass` path `BUG_BOUNTY_PLAN.md` cited** | See `github.com/owasp-amass/amass` for current install docs — the previous pass didn't capture Amass's own install command; check the repo directly before relying on a remembered one |

**Rate-limit discipline is not optional here.** The Perfume Shop's brief
states "Maximum 5 requests/second for automated testing" as an explicit
rule — treat that as the ceiling for every AS Watson brand (ICI PARIS
XL and Marionnaud's briefs didn't repeat the number in what was
captured here, but running nuclei/ffuf at default speed against a
5 req/s program is a plausible way to get flagged or banned before a
single report is filed). Set `-rate-limit 5` (nuclei) and `-rate 5` or
slower (ffuf) explicitly rather than trusting a tool's default.

**Not independently re-verified this pass, carried forward from
`BUG_BOUNTY_PLAN.md` unchanged:** Intigriti Quick Scope (Burp
extension) — still the right tool for staying inside scope
automatically, install via Burp's own BApp Store once Burp is running.

---

## 5. First week — concrete, no income promised

**Day 1 — accounts and paperwork, not testing.**
Register on Intigriti (`SOLO_REVENUE_ROUTES.md`/`BUG_BOUNTY_PLAN.md`
§1 has the exact flow). Run the ID check immediately — it can take time
and blocks payout later if deferred. While waiting, read ICI PARIS XL's
live in-dashboard brief in full — not this file's summary — and
cross-check it against what's quoted above; note anything that's
changed.

**Day 2 — toolchain and scope mapping, still not testing.**
Install the tools in §4. Run `subfinder` and `httpx` against
`iciparisxl.nl`/`.be`/`.lu` domains **only after confirming via the
live dashboard brief that passive subdomain enumeration is itself
permitted** — some programs restrict even passive recon to
explicitly-listed hosts; this file cannot confirm that rule from the
public brief alone. Build a written scope map: which Tier-1 hosts
exist, which respond, which look like the "e-commerce payment/order
flow" and "authorization/API" surfaces the brief explicitly asks for.

**Day 3 — read, don't scan: study the excluded list until it's
memorised.**
Every AS Watson brief lists the same ~20 excluded classes verbatim
(self-XSS, CORS on non-sensitive endpoints, missing headers, low-impact
CSRF, etc.). A newcomer's most common wasted week is finding and
reporting exactly these — they're excluded precisely because everyone
finds them first. Spend a day understanding *why* each is excluded
(what makes it low-impact) rather than looking for them.

**Day 4-5 — manual testing within the 5 req/s limit, on ICI PARIS XL
Tier 1 assets only.**
Work the account/checkout/order flow by hand in Burp: create a test
account (using real, your-own data — never someone else's), walk the
checkout process, inspect every request for authorization boundaries
(can one account see another's order? does the API trust a client-side
role claim?). This directly targets the brief's own named priorities
("Authorization flaws in API & Microservices," "Zero-click mass
customer account takeover," "Checkout/order process abuse"). Do not
run automated scans yet — hand-testing the highest-value flows first is
both lower-risk (no rate-limit violation) and more likely to find what
the program actually wants, per its own stated focus.

**Day 6 — if nothing found, run bounded automated recon, respecting the
rate limit.**
`nuclei -rate-limit 5` against confirmed live Tier-1 hosts for known
misconfigurations; `ffuf` at a conservative rate for hidden
endpoints/parameters on the API subdomain specifically (the brief's own
named focus). Log everything — a null result is still useful
information for day 7.

**Day 7 — write up or stand down, honestly.**
If something was found: write the report against the program's own
template before submitting anything, cross-check it isn't one of the
explicitly-excluded classes, and only then submit. If nothing was
found: that is a normal, expected week-one outcome per the honest odds
in `BUG_BOUNTY_PLAN.md` §3 — not a signal to escalate scope or speed.
Register on HackerOne and Bugcrowd in parallel (per
`BUG_BOUNTY_PLAN.md` §1's sequencing) so the following week has more
than one door open, and repeat the same methodology against The Perfume
Shop or Marionnaud next, since the AS Watson brief pattern is now known.

**What this file will not do: promise a dollar figure for week one.**
`BUG_BOUNTY_PLAN.md` §3 already established the honest baseline — this
is unpaid reconnaissance and skill-building for most newcomers over the
first months, run in parallel with other income, not as the income plan
itself.
