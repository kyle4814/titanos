# Global Remote-Work Platforms — Beyond the Already-Checked List

Researched 2026-09-03, same operator profile as `DEALS_SMALL_FISH.md` /
`DEALS_LIVE_CONTRACTS.md` (solo, Cairns AU, no certs, ABN held,
remote-capable, can build software fast with AI tooling). This file
goes wide, not deep on any one platform already covered: Freelancer.com/
.com.au (works, direct-fetch category pages), Upwork (403s), Guru
(login-gated), Truelancer/Workana (bot-walled), Toptal/Gun.io/Braintrust
(account + vetting required), RemoteOK (robots.txt names ClaudeBot
disallowed).

Five research passes ran in parallel (background agents), each on a
distinct category. Every finding below traces to an actual `robots.txt`
check and/or `WebFetch` this session. `WebSearch` ran out of budget
(200/200) partway through — flagged per-platform where that left a real
gap, not silently papered over. Nothing fabricated: where a page didn't
state a number, it's marked UNKNOWN, not guessed.

**No account created, no application submitted, no login attempted,
no User-Agent spoofed, anywhere in this research.**

---

## RANKED — real day rate ÷ entry barrier

### Tier 1 — best rate-to-barrier ratio, worth real time

| Rank | Platform | Rate | Entry gate | AU-eligible | URL |
|---|---|---|---|---|---|
| 1 | **YunoJuno** (UK) | **Published, exact**: Software Engineering £533/day, Cloud & Infra £566/day, AI & Automation £472/day, Data & Analytics £501/day (from their own 2026 Rates Report, averaged from "approved contractor profiles") | Self-service signup (`app.yunojuno.com/profile/onboarding/sign-up/`); "approved" implies a review step but mechanics not disclosed on public pages | UNKNOWN on residency — platform claims payment reach to "165+ countries" (a payments claim, not a registration-eligibility statement) | yunojuno.com |
| 2 | **Arc.dev** | Freelance **$15–$110+/hr** stated range; US-based freelancers cited at **$60–$250/hr**; international rates "vary significantly by location," no AU figure given | Two tracks. Freelance: technical interview or peer-programming session + final review (~1hr). No certification required. | **Yes, explicit** — site has a dedicated "Freelancers in Australia" category, the only platform in this sweep to name Australia directly | arc.dev |
| 3 | **Synack Red Team** | Partial, unconfirmed-current figures found: missions $25–50 (routine) to $100+ (ad-hoc), vulnerabilities $500–several thousand; one 2020-era source cited average $600–900/vuln — **treat as indicative, not current** | 5-stage published pipeline: resume review → technical assessment → background/ID check → behavioral interview → onboarding. **No certification required.** | Yes, implied — "hack from anywhere in the world with virtualized workspaces," no exclusion stated | synack.com |
| 4 | **Cobalt Core** | UNKNOWN exact figure — platform states "paid for your time and effort, not per vulnerability" (day-rate-like model) rather than bounty-per-bug | 5-stage pipeline: application → skills assessment → interview → ID/tax verification → ongoing peer review. **Cert optional, not mandatory** (OSCP/OSCE shown on profiles as enhancement only) | Implied international ("security professionals around the world") but not AU-confirmed specifically | cobalt.io |
| 5 | **HackerOne (base tier)** | UNKNOWN specific rate; site cites "up to $5K stipend per pentest engagement" and an aggregate "$380M+ Rewarded" (not a rate) | **Near-zero barrier for base signup** (name/username/email only). Paid tiers (Pentest-as-a-Service, "HackerOne Clear") are opaque about their own vetting — real money sits behind a second, undisclosed gate | Not stated either way | hackerone.com |

### Tier 2 — real but higher barrier, lower transparency, or narrower fit

| Platform | Rate | Entry gate | AU-eligible | Note |
|---|---|---|---|---|
| **Dice** (US job board) | **Published, exact**: e.g. $90–93/hr (Randstad Digital), $57–62/hr (Stefanini), $60–75/hr (Kaygen) for pentest/security-engineer contract roles | Free browsing, no account needed to see rate+listing; "Apply" requires login | Per-listing, not platform-wide — one posting AU/remote-friendly, another India-only, another DoD-flagged. US-centric market; work-auth eligibility is listing-dependent, genuinely UNKNOWN in aggregate | Strongest **published, real, current** rate numbers found in this whole sweep — worth a manual per-listing check |
| **Hack The Box Business (Talent Search)** | None published | **Not an application gate at all** — eligibility is earned by HTB platform rank (grind labs/CTFs for free, then employers browse and contact you directly) | Not addressed; "global talent pool ... from all over the world" | Structurally different from every other platform here: zero interview/cert gate, but real time investment in skill-proving content first. Featured client list (Synack, Booking Holdings) suggests real hiring volume. |
| **Expert360** (AU-headquartered) | UNKNOWN — experts "set their own hourly or day rate" | **Selective**: "individually assessed before joining... accept roughly 10% of applicants" | AU-headquartered, so plausibly AU-friendly, but no explicit statement found and application pages 404'd | Worth checking directly given AU HQ — the only platform in this sweep with a stated acceptance-rate number |
| **Freelancermap** (Germany) | No day rates published; platform pricing only (€0 free tier / €13.99/mo Premium) | **Open self-service registration**, no stated vetting | Not restricted by any stated rule; not AU-confirmed | Same character as Freelancer.com — open bidding, real listings, no rate floor guaranteed |
| **Talmix → High5** (rebranded 2023+) | UNKNOWN | "Pre-vetted, curated" consultants; actual criteria page 404'd | Claims "190 countries" market coverage (not an eligibility statement) | Real marketplace gates listings behind login entirely — nothing visible pre-account |
| **Alignerr** (AI/automation, see Category 5 below) | **Published, exact**: avg $80/hr, range $20–120/hr | Ordinary self-service signup, no cert disclosed | UNKNOWN, not excluded on the pages checked | Job titles, pay ranges, testimonials all public pre-account | The best rate-to-barrier ratio found in Category 5 — arguably belongs in Tier 1, held here pending AU-eligibility confirmation |

### Tier 3 — dead ends, hard exclusions, or genuinely blocked to this tooling

| Platform | Verdict |
|---|---|
| **Malt** (.com/.de/.es/.uk) | **HTTP 403 on every domain, including robots.txt itself** — a hard bot-protection block (Cloudflare), not a crawl-policy disallow. Completely unresearchable by this tooling. Needs a real browser. |
| **Comatch** | Dead as a standalone platform — `comatch.com` 301-redirects to a Malt marketing page. Acquired by Malt in 2023. |
| **Otta** | Dead — `otta.com` 301-redirects to `uk.welcometothejungle.com`, a different, general-hiring product. |
| **Hired** | Dead — `hired.com` 301-redirects to a generic LHH/Adecco corporate page with zero Hired branding. Absorbed, not independently usable. |
| **CyberSecJobs** | **Hard exclusion** — homepage states "U.S. citizenship and an active or current security clearance is required," operated on the same network as ClearedJobs.Net. |
| **ClearanceJobs** | **Hard exclusion, confirmed** — "the largest career network for professionals with federal government security clearance." US-clearance-only as expected. |
| **EU-Startups job board** | **HTTP 403 on every fetch attempt** (robots.txt and content pages both) — same access pattern as Upwork. Unresearchable by this tooling. |
| **AU/NZ-specific cybersecurity contract board** | **None found.** WebSearch quota ran out mid-check; Seek.com.au's contract filter 403'd; AustCyber redirects to a startup-ecosystem page, not a job board. Genuine gap, not a negative finding — worth one more pass with search budget restored. |
| **Wellfound** (ex-AngelList Talent) | Listings checked were full-time salaried roles only, no contract postings found. Not a contract lane. |
| **Pentester.com** | Not a researcher marketplace at all — it's a SaaS vuln-scanning product company with no careers/apply page in its nav. |
| **Proxify** | robots.txt is permissive but **every content page returned HTTP 403** — WAF/bot-gating on the actual pages. Blocked to this tooling. |
| **Andela / Turing / Lemon.io / Pesto** | Dev-focused marketplaces (Turing and Andela both now frame themselves as AI-engineering-specific), **no security track identified on any of the four**, rates mostly UNKNOWN or indirect (Andela: one example profile at $6,500–8,500/mo; Turing: AI-data-labeling task bounties, not dev rates; Lemon.io: a generic market-rate calculator, not their own pay card). AU eligibility unclear-to-absent (Lemon.io explicitly lists Europe/LatAm/US/Canada, omitting Australia). Listings gated behind login on all four. Lowest priority in this sweep — dev-only fit, opaque pay, unclear AU access. |
| **BreachLock** | "Certified In-House — CREST, OSCP, OSCE and more" language suggests certs matter more here than the marketplace platforms; no crowdsourced researcher-community model found (contrasts with Cobalt/Synack/Intigriti); careers page routes to an external Workable ATS, not fetched. |
| **Sprocket Security** | Reads as a direct-employment/contractor staffing page, not a skills-gated marketplace; "Open Positions" section was empty at fetch time. |
| **Intigriti Hybrid** | Landing page shows only a signup CTA and an "Active programs 400+" count — no rate, no stated vetting step visible pre-account. Genuinely under-researched, not negative. |

---

## Category 5 — AI/automation build work: real platforms found, superseding the earlier negative finding

Corrected 2026-09-03, same session, second pass. A dedicated background
agent later checked robots.txt + WebFetch for a wider set of AI-work
platforms and found real, published-rate marketplaces — the "no
dedicated marketplace exists" read below was premature. Left below for
the audit trail, corrected here:

| Platform | Rate | Entry gate | AU-eligible | Pre-account visible | robots.txt |
|---|---|---|---|---|---|
| **Alignerr** (alignerr.com) | **Published**: avg $80/hr, range $20–120/hr per role | Ordinary account signup (`app.alignerr.com/signup`) — no cert named on the public pages | Not excluded on the pages checked; UNKNOWN if enforced at application | Yes — job titles, pay ranges, testimonials all public | Open (`Disallow: /cgi-bin/`, `/*.pdf$` only) |
| **Braintrust — AI-specific roles** | **Published per-role**: ML Ops Engineer $140–200/hr, RLHF Healthcare Expert $100–180/hr, AI Annotator $20–40/hr, Staff ML Engineer $180–260/hr | Braintrust's general account gate applies (already logged elsewhere in this file); certification unlocks a smaller "AI-matched" qualified pool | UNKNOWN, not re-derived this pass | Yes — browse page is public | Open (`Allow: /`, `Disallow: /api/`) |
| **Surge AI** (surgehq.ai) | One published role: journalist contractor $200–400/hr; other roles unspecified but demand elite credentials (Pulitzer, VC partner, SC clerkship) — poor fit for an unaccredited generalist builder | Direct email application (talent@surgehq.ai) with background, no formal skills test disclosed | Remote, no exclusion stated; UNKNOWN | Yes, fully public workforce page | robots.txt empty (fully open) |
| **Contra** | Commission-free; rates are creator-set, not platform-published. Notable: page declares `Content-Signal: ai-train=no, search=yes, ai-input=yes` | Open profile creation, no vetting found | UNKNOWN | Yes — full portfolios, "AI Developer" category browsable without login | Open |
| **n8n Experts directory** | UNKNOWN | **Effectively closed** to a cold AU applicant right now: requires ≥3 already-active n8n customers, restricted to UK/Ireland/N.Europe/N.America | No (explicit region restriction excludes AU) | Directory browsable; application gate closed | Open |
| **Invisible Technologies** | No dollar figures published, only named US metro pay tiers, "market-adjusted" for international hires | Not described on the page reached; general careers process, UNKNOWN | UNKNOWN | Compensation philosophy is public but no rate figures | Open, narrow disallows |
| **Zapier Experts/Solution Partners** | Not published by Zapier itself (one partner profile mentions its own $297 session price, not a platform rate) | Application via `zapier.com/l/new-experts`, criteria not disclosed | UNKNOWN | Yes — full partner profiles public | Open, explicitly grants ClaudeBot |
| **Make.com Partner Program** | Not published | Requires completing Make's certification course | UNKNOWN | Directory browsing open; portal itself login-gated | Open |
| **Gitcoin** | N/A | N/A — **pivoted entirely to a grants/public-goods research directory**, no bounties or dev work remain. Ruled out. | — | — | Open |

**Corrected honest read:** Alignerr is the standout in this category —
real published $20–120/hr rates, visible without an account, ordinary
signup with no disclosed certification or skills test. Braintrust's
AI-specific roles pay well ($140–260/hr for ML/automation work) but sit
behind Braintrust's already-logged general account gate. Surge AI's
rates are real but its roles target credentialed subject-matter experts,
not a fast-build generalist. n8n's expert directory is a hard no right
now (closed pilot, wrong region). Gitcoin is dead as a bounty source.
Toloka and Handshake AI (the data-labeling brand, distinct from the
university-recruiting Handshake at joinhandshake.com) remain genuinely
**UNCHECKED** — flagged, not fabricated.

---

## ROBOTS.TXT VERDICTS (all hosts checked this session)

| Host | Verdict |
|---|---|
| yunojuno.com | Allowed except `/style-guide`, `/components`, `/partnerships/*`, `/client-offer`, `/test-page`, one case-study page, `/no-index/` |
| arc.dev | Allowed (`Allow: /`); only excludes `/resume/builder/`, `/cookies`, `/privacy`; rate-limits AhrefsBot and **ClaudeBot** (not a block) |
| synack.com | Allowed — only `/wp-admin/`, `*.pdf`, `/cdn-cgi/` blocked |
| cobalt.io | Allowed — narrow HubSpot preview-path blocks only |
| hackerone.com | Allowed — standard Drupal admin/login boilerplate only |
| dice.com | Allowed — standard admin/query-param disallow list |
| hackthebox.com | **Self-contradictory** — explicitly disallows ClaudeBot (and Amazonbot, Applebot-Extended, Bytespider, CCBot, Google-Extended, GPTBot, meta-externalagent) via one block, then grants `Allow: /` to all agents including the same named bots in another block |
| expert360.com | Allowed except `/template/`, `/nz/template/` |
| freelancermap.com | Fully open (`Disallow:` empty) |
| talmix.com / high5hire.com | Fully open, explicitly welcomes ClaudeBot/GPTBot/anthropic-ai/PerplexityBot by name |
| worksome.com | **Unverified** — fetch only surfaced the sitemap line, not the actual directive block |
| malt.com/.de/.es | **HTTP 403 on robots.txt itself** — hard block, not a disallow |
| comatch.com | 301-redirects (dead platform) |
| otta.com | 301-redirects (dead platform) |
| hired.com | 301-redirects, and robots.txt itself 404s (dead platform) |
| cybersecjobs.com | Allowed, `Crawl-delay: 10` — excluded on eligibility grounds regardless |
| clearancejobs.com | Blocks GPTBot explicitly; no ClaudeBot-specific rule — excluded on eligibility grounds regardless |
| eu-startups.com | **HTTP 403 on every path**, robots.txt included |
| wellfound.com | Allowed except auth/application-flow/profile/search paths |
| pentester.com | Fully open (`Allow: /`) |
| sprocketsecurity.com | Allowed generally; blocks a handful of specific blog URLs only |
| breachlock.com | Allowed, standard WordPress boilerplate disallows |
| intigriti.com | Fully open (`Allow: /`) |
| andela.com | Fully open — only a `Sitemap:` line, no Disallow at all |
| turing.com | Allowed generally — disallows `/api/*`, `/preview/*`, `/lp/*`, `/cloud/*`, a few named paths |
| lemon.io | Allowed for `*`/ClaudeBot; blanket-disallows ~20 named scraper bots (RyteBot, MJ12bot, Scrapy, etc.) |
| proxify.io | robots.txt itself permissive — but every actual content page 403'd (WAF layer separate from robots.txt) |
| pesto.tech | No robots.txt file exists (404) |
| contra.com | Allowed, narrow internal-path/redirect-param blocks only |
| zapier.com | Allowed generally, explicitly grants ClaudeBot/Claude-SearchBot full access |
| make.com | Allowed, standard app-path/query-param disallows |
| n8n.io | Allowed except `/cdn-cgi/` |

No host in this sweep returned a blanket `Disallow: /` for ClaudeBot except
Hack The Box's self-contradictory file. Malt and EU-Startups are hard
403-blocked at the network/WAF layer, not by robots.txt policy — same
pattern already seen with Workana in the prior session.

---

## THE HONEST BOTTOM LINE

**Best real leads from this sweep, in order:**

1. **YunoJuno** — the only platform with a full, exact, current day-rate
   table (£472–£566/day across relevant categories) and a low-friction
   self-service signup. AU-residency eligibility genuinely unconfirmed —
   worth 10 minutes to check the actual signup form.
2. **Arc.dev** — explicit Australia eligibility, real published rate
   range, a single ~1-hour technical interview as the only gate. The
   best-confirmed AU-accessible option in this entire sweep.
3. **Dice** — real, current, published USD/hr contract rates for
   security-engineer roles, zero account needed to browse — but US-market
   and AU work-eligibility is genuinely per-listing, not platform-wide.
4. **Synack / Cobalt** — no certification required, structured multi-stage
   vetting (skills test + interview, not gatekept by a credential), global
   framing. Rate data is thinner than YunoJuno/Arc/Dice but the entry gate
   is honestly the most merit-based of the security-specific platforms.
5. **HackerOne base signup** — near-zero barrier, but the actual paid
   programs sit behind a second, undisclosed vetting layer this pass
   couldn't see into.

**Genuine dead ends, confirmed this session, don't re-check:** Comatch,
Otta, Hired (all folded into other products or defunct), ClearanceJobs
and CyberSecJobs (US-clearance-gated), Pentester.com (not a marketplace).

**Genuinely blocked to this tooling, needs a real browser, don't
re-attempt with WebFetch:** Malt (all TLDs, 403 even on robots.txt),
EU-Startups (403 everywhere), Proxify (content pages 403 despite open
robots.txt).

**Category 5 (AI/automation build work) — corrected**: a second research
pass found real platforms, superseding the earlier "thin" read.
**Alignerr** ($20–120/hr, avg $80/hr, ordinary signup, no disclosed cert)
is the standout — real published rate, visible pre-account, near-zero
credentialing. **Braintrust's AI-specific roles** ($140–260/hr for
ML/RLHF/automation work) are well-paid but sit behind Braintrust's
already-logged general account gate. Vendor partner directories
(Zapier/Make) remain lead-gen, not a paying job board. Toloka and the
data-labeling "Handshake AI" brand are still genuinely unchecked.
