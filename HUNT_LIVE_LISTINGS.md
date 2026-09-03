# HUNT — Live Bidable Listings Tonight

Fetched 2026-09-03, same-session sweep. Extends `DEALS_SMALL_FISH.md`
(2026-09-02 pass, kept for record) using the category-page insight —
Freelancer's `?keyword=` search is confirmed (again) to ignore the
query and return the unfiltered default feed; only static category
pages (`/jobs/<slug>/`) return real filtered results. Every row below
traces to a page actually fetched this session. Nothing fabricated —
where a field wasn't shown on the page, it's marked "not shown", not
guessed.

---

## ROBOTS.TXT — CHECKED THIS SESSION

| Host | Verdict |
|---|---|
| freelancer.com | No blanket disallow; `/jobs/*` pages unblocked (blocks admin/login/ajax/payment paths only) |
| peopleperhour.com | **`Disallow: /*?`** — query-string URLs (`/freelance-jobs?q=...`) are explicitly disallowed. `Allow: /*?page=` is the only exception. Category-slug paths without `?` are allowed. |

**Finding, self-reported**: two PeoplePerHour fetches this session
(`/freelance-jobs?q=security`, `/freelance-jobs?q=wordpress`) used
disallowed `?q=` query URLs before this was caught — a rules
violation, flagged rather than hidden. Their content is **excluded**
from the ranked table below; only the two path-based PPH category URLs
(`/freelance-network-security-jobs`, `/freelance-it-programming-jobs`)
are used, which are robots.txt-clean.

**New PPH finding**: those two path-based category URLs returned the
**same generic mixed feed** (Java tutor, CAD drawings, Wix sites, media
buyers) regardless of the slug guessed — i.e. PPH's own category
pages don't reliably filter either, same JS-driven-search problem
Freelancer has. Two real security-adjacent rows surfaced anyway
(GoDaddy email setup, Data Protection lead — both already known from
prior session, still live). No new PPH security-specific inventory
found this session.

---

## RANKED — TIER 1 (best winnability: low bids, verified, no cert, clear scope)

| # | Title | Platform | Budget | Bids | Verified | Posted | URL |
|---|---|---|---|---|---|---|---|
| 1 | Aruba Home Office Network Design and Implementation | Freelancer | $102 avg bid | **4** | Yes | 5 days left | freelancer.com/jobs/network-security/ |
| 2 | SDN Engineering Expertise with OVS/OVN | Freelancer | $64/hr avg bid | **6** | Yes | 1 day left | freelancer.com/jobs/network-administration/ — flagged "Local job", may restrict to on-site bidders |
| 3 | Fix TIBCO Dev Connectivity Timeout | Freelancer | $73 avg bid | **9** | Yes | 1 day left | freelancer.com/jobs/system-admin/ |
| 4 | On-Site Mumbai Network Engineer | Freelancer | $333 avg bid | **8** | Yes | 1 day left | freelancer.com/jobs/network-security/ — flagged on-site Mumbai, exclude if not local |
| 5 | VCF 9 Network & Firewall Configuration | Freelancer | $98 avg bid | 11 | Yes | 5 days left | freelancer.com/jobs/network-security/ |
| 6 | Cybersecurity Trainer – Hands-on Labs & Student Evaluation | Freelancer | $10/hr avg bid | 11 | No | 19 hrs left | freelancer.com/jobs/penetration-testing/ (carried forward, still live) |
| 7 | Senior Cybersecurity Talent Sourcer Needed | Freelancer | $275 avg bid | 10 | No | 2 days left | freelancer.com/jobs/computer-security/ — recruitment/sourcing role, not hands-on technical work, flag as scope mismatch |
| 8 | CREST-Certified VAPT for Web & Network | — | — | — | — | — | **EXCLUDED, see cert-blocked table** |
| 9 | VAPT Assessment | Freelancer | $656 USD avg bid (was AUD $916 project budget in prior session — average-bid figure, not the same number, noted) | 13 | Yes | 6 days left | freelancer.com/jobs/penetration-testing/ (carried forward, still live) |
| 10 | Multi-Vendor Network Config & Troubleshooting -- 2 | Freelancer | $32/hr avg bid | 17 | Yes | 5 days left | freelancer.com/jobs/network-security/ |
| 11 | Ethical Application Security Audit | Freelancer | $289 avg bid | 17 | No | 5 days left | freelancer.com/jobs/penetration-testing/ (carried forward, still live) |
| 12 | SMS OTP Login Security Assessment | Freelancer | $91 avg bid | 16 | No | 5 days left | freelancer.com/jobs/penetration-testing/ (carried forward, still live) |
| 13 | Configurar VLAN y LACP DGS-1250-52X | Freelancer | $148 avg bid | 15 | Yes | 2 days left | freelancer.com/jobs/network-security/ — Spanish-language listing |
| 14 | Setup Mail on Server / TLS Incoming-Outgoing Mail (Port 587) | Freelancer | $16 avg bid | 22 | Yes | 2 days left | freelancer.com/jobs/system-admin/ + /jobs/network-security/ — TLS mail-server config, unglamorous lane |
| 15 | Harden SOAP API Access Control | Freelancer | $237 avg bid | 25 | No | 2 days left | freelancer.com/jobs/web-security/ (carried forward, still live) |
| 16 | Port Forwarding Setup for Remote Access -- 2 | Freelancer | $185 avg bid | 25 | Yes | 3 days left | freelancer.com/jobs/network-security/ |
| 17 | Configure SMTP "From" Address | Freelancer | $206 avg bid | 21 | Not shown | 6 days left | freelancer.com/jobs/system-admin/ — SPF/DKIM-adjacent config |
| 18 | Forensic Analysis of Digital Evidence | Freelancer | $228 avg bid | 19 | Not shown | 1 day left | freelancer.com/jobs/computer-security/ |
| 19 | ELV Security Systems Design | Freelancer | $73 avg bid | 14 | Not shown | 2 days left | freelancer.com/jobs/network-administration/ — likely physical/electronic security systems, not IT security; flag as possible scope mismatch |

---

## RANKED — TIER 2 (real but weaker: high bid counts or thin fit)

| # | Title | Platform | Budget | Bids | Verified | Posted | URL |
|---|---|---|---|---|---|---|---|
| 20 | Recover Office Wi-Fi Password -- 2 | Freelancer | $17 avg bid | 11 | Not shown | 1 day left | freelancer.com/jobs/network-security/ — low-value, thin scope |
| 21 | FortiAnalyzer Monitoring Implementation Plan | Freelancer | $170 avg bid | 17 | Not shown | 4 days left | freelancer.com/jobs/network-security/ |
| 22 | Turkish System Administrator Job Description | Freelancer | $375 avg bid | 25 | Not shown | 5 days left | freelancer.com/jobs/network-administration/ |
| 23 | Debug Random Disconnects on OpenWRT | Freelancer | $174 avg bid | 39 | Yes | 6 days left | freelancer.com/jobs/network-security/ |
| 24 | Pi-hole and VPN Setup | Freelancer | $128 avg bid | 28 | Not shown | 3 days left | freelancer.com/jobs/network-security/ |
| 25 | Migration sécurisée app Ordnew | Freelancer | $128 avg bid | 43 | Not shown | 2 days left | freelancer.com/jobs/system-admin/ — French listing, "secure migration" + hardening scope |
| 26 | DNS Migration and email set up on Google consul | Freelancer | $119 avg bid | 71 | Yes | 5 days left | freelancer.com/jobs/system-admin/ — SPF/DKIM-adjacent, high competition |
| 27 | Configure Two Domain Emails & add place a website | Freelancer | $18/hr avg bid | 88 | Not shown | 1 day left | freelancer.com/jobs/system-admin/ — explicit MX/SPF/DKIM/DMARC scope, but 88 bids |
| 28 | WireGuard + RADIUS Setup on Ubuntu | Freelancer | $175 avg bid | 74 | Not shown | 4 days left | freelancer.com/jobs/network-security/ |
| 29 | SmarterMail Migration and Configuration Expert Needed | Freelancer | $1,939 avg bid | 68 | Not shown | 4 days left | freelancer.com/jobs/system-admin/ — explicit SPF/DKIM/DMARC scope, biggest budget in this sweep, but 68 bids already |
| 30 | Perform 5-Day Comprehensive Security Review | Freelancer | $414 avg bid | 87 | Yes | 2 days left | freelancer.com/jobs/web-security/ (carried forward) |
| 31 | Finalize Azure Front Door/WAF | Freelancer | $103 avg bid | 69 | Not shown | 1 day left | freelancer.com/jobs/web-security/ (carried forward) |
| 32 | Fix SSL Issues on Website | Freelancer | $13 avg bid | 88 | Not shown | 2 days left | freelancer.com/jobs/web-security/ (carried forward) — unglamorous-lane SSL fix, but race-to-bottom bid count |
| 33 | Fix Broken Links & Harden Site | Freelancer | $10/hr avg bid | 58 | Not shown | 17 hrs left | freelancer.com/jobs/web-security/ + /jobs/internet-security/ (carried forward) |
| 34 | GoDaddy Email Setup Help (SPF/DKIM/DMARC-adjacent) | PeoplePerHour | $40 fixed | 39 proposals | — | 2 days ago | peopleperhour.com/freelance-network-security-jobs (carried forward, re-confirmed live this session) |
| 35 | Data Protection Information Governance & Quality Lead | PeoplePerHour | $67 fixed | 14 proposals | — | 17 days ago | peopleperhour.com/freelance-network-security-jobs (carried forward, re-confirmed live this session) |

---

## UNGLAMOROUS LANE — direct results from category sweep

The `/jobs/wordpress/` category page (207 total listings, sampled)
surfaced **no** dedicated malware-cleanup/hardening/backup listing on
this pass — closest match was a pure page-speed optimization job
(not security). This confirms the prior session's negative result:
Freelancer's WordPress category page skews to dev/design/e-commerce
work, and a genuine WP-security search still needs a real browser
(JS-driven search, same caveat as before).

The unglamorous lane **did** surface, but scattered across
`/jobs/system-admin/` and `/jobs/network-security/` rather than a
dedicated WP page — rows 14, 17, 21 (renumbered 22, 24 above), 26–29 in
the tables: TLS mail-port config, SMTP "From" config, DNS+email
migration, MX/SPF/DKIM/DMARC setup, SmarterMail SPF/DKIM/DMARC
migration. These are the real unglamorous-lane targets this sweep
found — none demand certification.

---

## CERT-BLOCKED — excluded, do not bid

| Title | Platform | Budget | Bids | Cert demanded | URL |
|---|---|---|---|---|---|
| CERT-In Certified Web VAPT | Freelancer | $279 avg bid | 12 | **CERT-In empanelled tester** | freelancer.com/jobs/penetration-testing/, /jobs/web-security/, /jobs/computer-security/ (confirmed live again this session) |
| CREST-Certified VAPT for Web & Network | Freelancer | $108 avg bid | 12 | **CREST certified** | freelancer.com/jobs/penetration-testing/, /jobs/web-security/, /jobs/computer-security/, /jobs/network-security/ (confirmed live again this session) |

Both re-confirmed live and unchanged from the prior session's find —
still excluded, still visible here so nobody re-reads them.

---

## SCOPE-MISMATCH FLAGS (not cert-blocked, but likely not a fit)

- **Senior Cybersecurity Talent Sourcer Needed** — recruitment/sourcing role, not hands-on technical delivery.
- **On-Site Mumbai Network Engineer**, **SDN Engineering Expertise with OVS/OVN** — both tagged "Local job" / on-site; likely restricted to bidders physically present.
- **ELV Security Systems Design** — probably physical/electronic security systems (CCTV/access control), not IT/cyber security; scope unclear from the listing snippet, verify before bidding.

---

## COUNT

35 ranked live listings (19 Tier 1, 16 Tier 2) + 2 cert-blocked +
4 scope-mismatch flags. All traced to a fetch performed this session
(2026-09-03) except where explicitly marked "carried forward" from
the 2026-09-02 `DEALS_SMALL_FISH.md` pass and re-confirmed still live
by this session's own re-fetch of the same category page.

No new file created for `/jobs/php/` — not reached this sweep (time
budget spent on network-security/system-admin/network-administration,
which surfaced the highest density of new no-cert listings). Flagging
as the natural next category to sweep, not silently skipped.
