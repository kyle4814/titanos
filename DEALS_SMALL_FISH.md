# Small Fish — Live Bids Tonight (Wide Sweep)

Researched 2026-09-03, same session as `DEALS_LIVE_CONTRACTS.md` (which
already confirmed Freelancer.com.au direct-fetch works and found the
VAPT Assessment / Ethical Application Security Audit listings — not
re-derived here, only cross-checked). This file goes wider: more
Freelancer categories, PeoplePerHour/Guru/Truelancer/Workana,
Codementor/Toptal/Gun.io/Braintrust entry requirements, and the
unglamorous WordPress/SSL/DNS-email lane.

Every row traces to a URL actually fetched this session
(2026-09-03). Nothing fabricated. `robots.txt` was checked for every
host before fetching job-listing pages.

---

## ROBOTS.TXT VERDICTS (checked before any listing fetch)

| Host | Verdict |
|---|---|
| freelancer.com / freelancer.com.au | Allowed for job pages (blocks only `/ajax/`, `/sellers/placebid.php`, login-fast endpoints) |
| peopleperhour.com | Allowed (blocks query-string URLs `/*?`, `/directory`, `/job/bidders*` — direct category/search paths are fine) |
| guru.com | robots.txt fully open, no disallow |
| truelancer.com | Not a robots.txt block — the site itself returns a Vercel bot-challenge page (JS proof-of-work) to any non-browser fetch, including the robots.txt request itself. Effectively unfetchable by this tooling. |
| workana.com | Allowed (blocks only `/api/`, login/signup query variants) |
| codementor.io | Allowed |
| toptal.com | Allowed (blocks `/api/`, `/administrator/`, a few asset paths) |
| gun.io | Allowed |
| usebraintrust.com | Allowed (`Allow: /`, blocks only `/api/`) |

No host in this sweep returned a blanket `Disallow: /` — the blocker
this session hit was JS-rendering/bot-challenge/wrong-URL-guess, not
robots.txt policy, except Truelancer which is a hard bot-wall.

---

## RANKED LIVE LISTINGS

Ranked by low bid count + no cert demanded + clear scope. Budgets as
displayed by the fetch (Freelancer shows "average bid" on some views,
"budget" on others — noted per row, since they are not the same number
and conflating them would overstate what's verified).

### Tier 1 — best realistic targets tonight

| # | Title | Platform | Budget | Bids | Cert demanded | URL |
|---|---|---|---|---|---|---|
| 1 | VAPT Assessment | Freelancer.com.au | AUD $916 (project budget) | 13 | No | freelancer.com.au/jobs/penetration-testing |
| 2 | Ethical Application Security Audit | Freelancer.com.au | AUD $403 | 17 | No | freelancer.com.au/jobs/penetration-testing |
| 3 | Cybersecurity Trainer – Hands-on Labs & Student Evaluation | Freelancer (.com / .com.au) | $10–14/hr (avg bid) | 11 | No | freelancer.com/jobs/penetration-testing |
| 4 | SMS OTP Login Security Assessment | Freelancer.com.au | AUD $127 | 16 | No | freelancer.com.au/jobs/penetration-testing |
| 5 | Harden SOAP API Access Control | Freelancer (.com / .com.au) | ~$237–330 | 25 | No | freelancer.com/jobs/web-security |

These five carry forward from (1,2,4,5) or corroborate (3) the prior
session's `DEALS_LIVE_CONTRACTS.md` findings — re-fetched this session
and still live, same bid counts, confirming they're genuinely open
right now, not stale.

### Tier 2 — real but weaker (high competition or thin scope)

| # | Title | Platform | Budget | Bids | Cert demanded | URL |
|---|---|---|---|---|---|---|
| 6 | Perform 5-Day Comprehensive Security Review | Freelancer.com | $414 USD (avg bid) | 88 | No | freelancer.com/jobs/web-security |
| 7 | Finalize Azure Front Door/WAF | Freelancer.com | $103 USD | 69 | No | freelancer.com/jobs/web-security |
| 8 | Fix SSL Issues on Website | Freelancer.com | $13 USD | 88 | No | freelancer.com/jobs/web-security |
| 9 | Add Subscriptions, Accounts, Database and Security to Website | Freelancer.com | $140 USD | 142 | No | freelancer.com (web-security / malware-removal search feed) |
| 10 | Fix Broken Links & Harden Site | Freelancer.com | $10/hr | 58 | No | freelancer.com/jobs/web-security |
| 11 | GoDaddy Email Setup Help (SPF/DKIM/DMARC-adjacent) | PeoplePerHour | $40 | 39 proposals | No | peopleperhour.com (security-jobs search) |
| 12 | Data Protection Information Governance & Quality Lead | PeoplePerHour | $67 | 14 proposals | No | peopleperhour.com (security-jobs search) |
| 13 | Android Lab-Environment RAT PoC Solution | Freelancer.com.au | AUD $35 | 18 | No | freelancer.com.au/jobs/penetration-testing (2-hour window — likely gone by the time this is read) |

Row 9 and 13 are borderline for a solo no-cert operator: #9 is 142 bids
(race to the bottom), #13 had a 1–2 hour window when fetched — flagged,
not recommended, but genuinely live at fetch time.

### CERT-BLOCKED — excluded, do not bid

| Title | Platform | Budget | Bids | Cert demanded |
|---|---|---|---|---|
| CERT-In Certified Web VAPT | Freelancer.com.au | AUD $389 | 12 | **CERT-In** |
| CREST-Certified VAPT for Web & Network | Freelancer.com.au | AUD $151 | 12 | **CREST** |

Both explicitly name a credential he doesn't hold. Visible, not wasted
effort to identify, but wasted effort to bid on — flagged and excluded
per the task rule, not silently dropped.

---

## PLATFORM-BY-PLATFORM FINDINGS

### Freelancer.com / .com.au — the only platform that reliably surfaced real listings
Category pages (`/jobs/penetration-testing/`, `/jobs/web-security/`)
return real, current listings on direct fetch — confirmed again this
session, same as the prior session's finding. **Keyword search URLs
(`/search/projects?keyword=...`) do NOT filter** — fetching
`?keyword=malware%20removal` and `?keyword=SSL%20certificate` both
returned the identical generic 50-listing feed (verified: same titles,
same order, same bid counts, in both fetches), meaning Freelancer's
search requires client-side JS to actually apply the filter and the
static fetch just gets the unfiltered default feed. **This is a real
tooling limitation, not a "no matching jobs" finding** — a genuine
WordPress-security/SSL/malware search on Freelancer needs a real
browser. The category-page approach (used for Tier 1/2 above) is the
only search method that worked.

`/jobs/wordpress-security/` and `/jobs/wordpress/` category pages
returned generic WordPress dev/design/e-commerce jobs with no dedicated
security/hardening/malware-cleanup listings visible in what rendered —
a genuine negative result for that specific category page, not
necessarily proof none exist (same JS-search caveat applies).

### PeoplePerHour — partially fetchable, weak security-specific yield
robots.txt is clear. Direct category URL guesses failed
(`/freelance-security-jobs` → 403); the working path was a search-style
URL (`/freelance-jobs?q=penetration%20testing`), which returned a
generic 51-result mixed feed with no dedicated pentest listings and
only two security-adjacent rows (GoDaddy email setup, data-protection
lead — both in Tier 2 above). Same JS-driven-search caveat as
Freelancer likely applies.

### Guru.com — robots.txt open, but the site itself gates listings behind login
`/jobs/security` and `/d/jobs/q/penetration-testing/` (guessed path)
both returned only the login page, no listings. **This is a real
finding, not a fabricated one**: robots.txt permits the crawl, but
Guru's job-board content is not served to an unauthenticated fetch —
functionally the same barrier as Upwork's 403, achieved differently.
Needs a real logged-in browser session to check.

### Truelancer — hard-blocked, not a robots.txt disallow
Every fetch (including the robots.txt request itself) returned a
Vercel "Security Checkpoint" JS proof-of-work challenge page. No
content, no robots.txt text, nothing usable. Cannot be checked by this
tooling at all.

### Workana — robots.txt open, but URL guesses failed
`/en/jobs?category=it-programming&query=security` returned 403 despite
robots.txt allowing the path pattern — likely a Cloudflare/WAF layer
separate from robots.txt (same pattern AusTender showed in the prior
`tender_radar.py` finding: robots.txt permission and actual WAF
behaviour are two different gates). Not resolved this session — needs
either the correct canonical URL or a real browser.

### Codementor, Toptal, Gun.io, Braintrust — entry requirements
- **Toptal**: robots.txt open. `/talent/apply` fetched successfully and
  shows the actual signup form (name/email/password, role selection
  across 9 categories, LinkedIn signup option) — but the page itself
  does not state the screening steps or show any open live work; Toptal
  is known (background knowledge, not verified this session) to run a
  multi-stage vetting funnel (language/personality screen, in-depth
  skill review, live screening call, test project) before a freelancer
  can see or bid on client work at all — this is a real barrier for
  "tonight," not a same-day option.
- **Codementor**: robots.txt open, but `/become-a-mentor` 404'd —
  wrong URL guess, not re-attempted. Unresolved.
- **Gun.io**: robots.txt open, but `/for-developers/` 404'd — wrong URL
  guess, not re-attempted. Unresolved.
- **Braintrust**: robots.txt open (`Allow: /`), but `/how-it-works`
  404'd — wrong URL guess, not re-attempted. Unresolved.

None of these four showed live open work to an unauthenticated fetch
regardless of URL success — all four are known to require an account
(and for Toptal/Gun.io, a vetting pass) before any job is visible, so
none is a same-night option even where the site itself is fetchable.

---

## THE HONEST BOTTOM LINE

**Real, live, bid-tonight count: 13 rows above (11 usable + 2
cert-blocked-and-excluded)**, all from Freelancer.com/.com.au and
PeoplePerHour — the only two platforms that actually served listing
content to an unauthenticated fetch this session. Five of those
(Tier 1) are genuine repeat-confirmation of the prior session's
findings, still live, same bid counts — good signal they're real,
current projects, not stale cache. The unglamorous lane (WordPress
hardening, SSL, SPF/DKIM/DMARC) did **not** turn up a strong dedicated
listing on any platform this session — the closest hits (Fix SSL
Issues $13/88 bids, GoDaddy Email Setup $40/39 proposals) are real but
weak (high competition, thin budget). This is a genuine negative
result for that specific ask, most likely explained by Freelancer's
and PeoplePerHour's keyword-search both requiring JS the fetch tool
can't run — the category-browse method that worked for pentest/
web-security wasn't available for a WordPress-security-specific
category.

**Best realistic targets tonight, in order: VAPT Assessment ($916 AUD,
13 bids), Ethical Application Security Audit ($403 AUD, 17 bids),
Cybersecurity Trainer ($10–14/hr, 11 bids).**

## WHAT WASN'T CHECKED / NEEDS A REAL BROWSER

Guru.com (login-gated), Truelancer (bot-walled entirely), Workana
(WAF 403 despite open robots.txt), a genuine WordPress-security/SSL/
malware keyword search on Freelancer or PeoplePerHour (search requires
JS on both), and the correct URLs for Codementor/Gun.io/Braintrust
informational pages. None of these are "checked and empty" — they are
"tooling couldn't reach it," which is a different, honestly-reported
gap.
