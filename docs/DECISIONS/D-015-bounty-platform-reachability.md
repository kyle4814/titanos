# D-015 — Bug-bounty platform reachability: only YesWeHack and Immunefi
# are readable by an honest automated agent. The other three majors are
# JS SPAs / login-gated and need Kyle's browser.

STATUS: DECISION RECORDED — NO MODULE BUILT (a reachability map, not a
build). Records a verified negative so future cycles do not re-probe the
same three platforms.
AGENT: autonomous ops cycle
DATE: 2026-09-03

## THE QUESTION

Bug bounties are the income route that best fits the operator's profile:
no company, references, insurance or certifications required. Two
platforms are already covered — YesWeHack (`mouth_bounty_yeswehack`, a
public API) and Immunefi (added 2026-09-03, program data server-embedded
in the page). This cycle asked whether the OTHER major Western platforms
— HackerOne, Bugcrowd, Intigriti — can be swept the same way, to grow the
roster.

## WHAT WAS TRIED, LIVE, 2026-09-03 (honest UA, robots respected)

| Platform | robots | directory page | verdict |
|---|---|---|---|
| **HackerOne** | `Allow` all (only a Sitemap line) | `/opportunities/all` and `/directory/programs` both return a **~1.8 KB JS shell** — zero program data server-side | **SPA — not automatable** |
| **Bugcrowd** | disallows only `/*?preview`, `/external_redirect` | `/engagements` is 108 KB but a marketing/listing shell — 6 "bounty" hits, no embedded program records | **SPA — not automatable** |
| **Intigriti** | empty disallow | `app.intigriti.com/researcher/programs` is a **6 KB shell** on the app subdomain, behind login | **SPA + login — not automatable** |

None was blocked by robots. The block is architectural: all three render
their program directories client-side (and Intigriti's is behind an
account). Reconstructing them by calling their internal GraphQL/JSON
endpoints was **declined** — the same discipline recorded for udbud.dk
(D-014-adjacent) and ADB CMS: when a site does not serve the data
statically and publishes no scraping API, an honest agent records the
SPA boundary rather than reverse-engineering the private endpoint its own
frontend uses.

## THE DECISION

- **Automatable bounty coverage = YesWeHack + Immunefi.** Those two are
  the sources this repository can sweep unattended, and both are wired.
- **HackerOne, Bugcrowd, Intigriti = human-browser only.** They are not
  a block to work around; they are a one-time human step (Kyle opens an
  account and browses the directory). Recorded so a future cycle does not
  re-probe them expecting a different result.
- **No new mouth built.** Building a HackerOne/Bugcrowd mouth would mean
  either driving a headless browser (out of scope, and fragile) or
  hitting a private GraphQL endpoint (declined above). Neither is
  justified for a source Kyle can browse himself once he has an account.

## SIDE FINDING, RECORDED

Re-swept the live bounty board the same day: 64 signals, the one flagged
`new` was a Hacker News "who is hiring" full-time role (ChainSecurity,
Zurich, visa) — employment, not a solo-actionable bounty; not added to
the roster. Ant Group remains the top uncontested target. The
`income_watch` newcomer's-edge sort was also verified correct against a
suspected defect: known-0-report programs (Ant Group) sort ABOVE
unknown-contest gigs, which sort last — the documented behaviour, not the
inversion first suspected.
