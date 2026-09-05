# OPS BOARD — every live opportunity, what it's worth, what it needs

Compiled 2026-09-02, last re-swept 2026-09-04. Every figure here was
read off a primary source during this campaign, not recalled. Where
something is unknown it says UNKNOWN — that is a real state, not a gap
someone forgot to fill.

**Round 30, 2026-09-06 — fixed a red push (mouth_nlnet was unreachable) +
lesson.** Round 29 pushed `9ab3697` on the fast-verify path — and the background
full-suite checkpoint caught it RED: `mouth_nlnet.py` was added but never wired,
so the reachability gate (`test_every_real_unreachable_module_has_an_intent`)
failed inside the real-repo sigil path, which fast-verify skips. Diagnosed
honestly (isolated `test_sigil` → nested foundation → the exact test), NOT
re-run-till-green. Fixed by WIRING it (finish the door): `operator_cli nlnet`
shows NLnet's live open call/deadline, so `mouth_nlnet` is reachable AND useful.
**LESSON (now firmer in velocity config): the full suite is mandatory before
push when touching shared/core code — the fast-verify subset is only safe for a
truly isolated add.** Full suite green (4,272 tests); remote back to green.

**Round 29, 2026-09-05 — 🎯 FIRST GENUINELY-WINNABLE SOURCE WIRED: NLnet/NGI
Zero.** Kyle called out (correctly) that the finder was a keyhole — 5 saturated
gov feeds — while "the internet is a cesspool of cash." Proved the well is deep
(grants.gov alone: 215 cyber / 640 tech open live), but grants.gov is US-entity
gated = not winnable for a solo Aussie. Found and wired the one that IS:
**NLnet/NGI Zero** — verified live on nlnet.nl: **€5,000–€50,000 R&D grants,
"available to both individuals and organisations"** (no US-entity/turnover/
reference wall), rolling calls, next deadline **2026-11-03**, funding
open-source security/tech **the system can help BUILD**. This is the single best
fit for the Kyle+system model. Built `foundation/mouth_nlnet.py` (static page,
gated socket, deadline parsed/None-if-UNKNOWN; 6 tests) + added `NL_NLNET` to
`team_targets` so it flows to the desktop folder. README 4,298→4,304. Verified
fast per the velocity rule (module+control-plane+manifest+all downstream
consumers green); full suite as background checkpoint. NEXT: more winnable
sources (bug bounties, EU-open-to-non-EU, inferred-demand) + a fit-filter.

**Round 28, 2026-09-05 — 🟢 FIRST-DOLLAR LEVER OPERATIONAL: Kyle's 150k leads →
ranked hot prospects.** The lead engine needed a source; Kyle already has one —
`~/titanos_leads_FINAL_20260701.csv`, **150,047 real Australian businesses**
(business_name, email, website, category, suburb, state). Built
`foundation/lead_source.py` `domains_from_csv()`: extracts business domains from
the website column (email fallback, drops free-mail providers), normalises,
de-dupes, polite `limit`. Wired `operator_cli leads --from-csv LEADS.csv --limit
N`. **RUNTIME-VERIFIED live end-to-end: 3 leads from the real CSV → 2 graded D**
(wide open, spoofable, call-first). The chain is now whole: real leads → domains
→ email-security triage → ranked hot-lead sheet with a provable hook → (Telegram
live) can ping Kyle. 7 tests, pure parsing (synthetic CSV, never his data).
README 4,291→4,298.

**Round 27, 2026-09-05 — 🟢 THE TELEGRAM LOOP IS LIVE (first real external
ping sent).** Kyle: "it's all wired up already, please use it." It was — I was
reading the wrong var names. His moneyprinter bot creds live in `~/.titanos_env`
as `TELEGRAM_BOT_TOKEN` + `TELEGRAM_DM_ID` (not `TELEGRAM_CHAT_ID`). Fixed:
accept `TELEGRAM_DM_ID` as a chat-id alias, and `resolve_operator_credentials()`
falls back to `~/.titanos_env` (TELEGRAM_* keys only, no os.environ mutation) so
autonomous runs reach Kyle without sourcing. **RUNTIME-VERIFIED: `operator_cli
alert` sent the first real ping to Kyle's phone ("alert sent to Kyle").** The
async human-in-the-loop is now genuinely connected end-to-end. 7 tests; fixed a
default-arg binding bug caught on the way. README 4,287→4,291. ⚠️ SECURITY: the
bot token briefly surfaced in a dev test error (that binding bug) — recommend
Kyle rotate it via @BotFather as a precaution; new token goes in the same
`~/.titanos_env`.

**Round 26, 2026-09-05 — built `lead_engine`: prospect triage (the first-dollar
lever).** Execution-phase build toward the reality anchor (first real dollar =
Kyle closing a warm lead). `foundation/lead_engine.py` `triage_domains(domains)`
assesses each domain's public email security (reuses `email_security_report`,
gated DoH) and ranks HOTTEST-FIRST by spoofability: no/weak SPF+DMARC = email
forgeable in their name = a real, provable, urgent hook. Grade D = 🔥🔥🔥 call
first; a secure domain is NOT a lead and never inflated into one; the sheet
stays honest (posture signal not a full audit; Kyle makes the contact
lawfully). Wired as `operator_cli leads --domains / --from FILE`.
RUNTIME-VERIFIED live (example.com → grade D on fire; github.com → C warm).
6 tests. README 4,281→4,287. Feeds Kyle's own sales motion; the missing piece
is a *source* of real business domains (his leads, or a future lead-source
mouth) — the tool triages whatever list it's given.

**Round 25, 2026-09-05 — built the keystone: `telegram_approval` (async
human-in-the-loop).** Kyle gave the greenlight and confirmed his moneyprinter
Telegram bot is already wired — so this builds the piece that plugs in.
`foundation/telegram_approval.py`: `request_approval(ApprovalRequest)→Decision`
fires an Approve/Deny card for any gated action (money/credentials/legal/
outbound/irreversible) — FAIL-CLOSED (no creds → UNAVAILABLE, no tap → TIMEOUT,
deny → DENIED; only an explicit tap is APPROVED, and only `APPROVED.is_approved`
is True, so a gated action never proceeds by default; the card gates, it never
legalises). `alert_operator(headline, detail)` pings Kyle to come sharpen swords
mid-op. Reuses `telegram_notify`'s gated socket + creds; plugs into the existing
bot via TELEGRAM_BOT_TOKEN/CHAT_ID. Wired as `operator_cli alert`. 11 tests,
network-free. This is the connector that makes "runs semi-autonomously, taps
Kyle only for the gates" real. README 4,268→4,279. Next: the daemon that calls
it, and the lead engine feeding it. NOTE — the opportunity list must keep
growing (Kyle: "there's a LOT neither of us is aware of yet"); each cycle widens
it, never treats it as closed.

**Round 24, 2026-09-05 — refocused opp-drop + rewrote `/next` to Kyle's loop.**
Kyle corrected the division of labour: he's the closer (his own leads + offer
for titanos.tech), he does NOT want a cold-call kit — he wants the system to
HUNT the world for opportunities he can apply for, drop them on his desktop, and
he applies/actions/authorises then goes back to selling; then NEXT and it hunts
another 2–4 hours. Cut the `SELL_TITANOS` cold-call kit from opp-drop;
START_HERE now leads with opportunities-to-apply-for ranked by deadline, one
action per item. Rewrote `.claude/commands/next.md` to that loop: hunt broad +
widen the net each run, extract truth (UNKNOWN never invented), drop the
package, prove green, two-line report — the folder is the product, Kyle never
has to talk to the system to work it. Desktop refreshed (23 files). Standing
next-work: widen the hunt — a grants mouth, a bug-bounty source, more tender
portals — so the folder fills with more real fish each run. README 4,269→4,268.

**Round 23, 2026-09-05 — built `opp-drop`: the desktop opportunity package
(the hunter's hand-off to the closer).** Kyle's directive: stop making him talk
to the system — every run, drop a ready-to-work package on his desktop so he
just opens it and cold-calls / sells / submits. Built `foundation/opp_drop.py`
+ `operator_cli opp-drop`: writes/refreshes a `TITAN_OPPORTUNITIES` folder on
the desktop with START_HERE (top moves), one ready-to-file pack per live tender
(22), and a `SELL_TITANOS/` cold-call kit — the pitch, the script, and the
`security-report` command that generates a prospect's free email-security hook
(a domain grading C/D = spoofable = hot lead). RUNTIME-VERIFIED: 25 files
written to the real desktop (`/mnt/c/Users/tech2/OneDrive/Desktop/`). Honest —
packages only reachable opportunities, names unbuilt streams (grants, on-chain)
as unbuilt, writes files only (never contacts anyone). Wired into `/next`
end-of-cycle. 7 tests (network-free). README 4,262→4,269. Next: broaden the
hunt (a grants mouth, a local-business lead source for the cold-call list).

**Round 22, 2026-09-05 — built `email_security_report`: the first sellable
automated deliverable (priority 5, new capability + defect fixed).** Kyle's
model is "the system delivers, I sell and click" — so the engine needs a
product. Built `foundation/email_security_report.py`: give it a domain, it
produces a professional email-security posture report (SPF/DMARC/DKIM/DNSSEC/
MX/MTA-STS) from public DNS only, via gated DNS-over-HTTPS (dns.google) — no
credentials, no intrusion, no new deps, no raw sockets, same gate as every
other fetch. Honest: absent controls report FAIL (never hand-waved), weak ones
WARN not PASS, scope disclaimer says posture-check not full audit. Wired as
`operator_cli security-report --domain X`. RUNTIME-VERIFIED live against real
domains (github.com → grade C, real gaps found). Defect caught in the live run
and fixed: a substring match read `p=reject` out of `sp=reject` and mis-graded
p=quarantine as PASS — now parses the actual `p=` tag; regression test added.
8 tests. This is the same fetch→extract→structure→report loop as the tender
radar, pointed at a new target — proof the engine generalises. README
4,254→4,262.

**Round 21, 2026-09-05 — built `submission_pack` (Kyle asked for one-click
command submissions).** The honest answer: the clicking was never the wall —
the bids aren't written, and that needs the team's real facts. Built the
machinery that drives to the submit line: `foundation/submission_pack.py`
`build_submission_pack(target, TeamProfile)` → portal + login URL, the real
per-portal step sequence (eTenders/TED-buyer/Find-a-Tender), the upload
checklist from the notice's quoted requirements, and an ESPD/qualification
answer sheet filled from the profile. Honest by construction: an unsupplied
fact is UNKNOWN and listed under MISSING (never invented); the final step is
ALWAYS the human Submit (filing a public tender is a binding legal act a person
must attest); no network, no credentials, no account creation. Wired as
`operator_cli submission-prep --target <id> [--profile team.json] [--out]`. 8
tests. What stays Kyle's by design: the login, the Submit click, and the actual
bid content (pricing/references/signed ESPD). Caught the README-drift→sight
cascade again (the +8 tests), fixed via autonomy_loop before push.

**Round 20, 2026-09-05 — deduped the redundant real-repo sigil computes
(priority 5), full gate now 475s.** Last round flagged that the full suite
still recomputed the SAME real-repo sigil ~4× (setUpClass pair + two reconcile
tests), each ~226s of shelling out over every subsystem. Fixed: `reconcile_
sigil(repo_root, previous, current=None)` now accepts an already-measured
`Sigil` and skips the recompute (a real win for the SIGIL.md update flow too),
type-gated so a hand-edited `RecordedSigil` is refused. `test_sigil` computes
the real sigil ONCE (lazy `real_repo_sigil()` cache) shared by the reconcile
tests; the determinism test still computes a second independent sigil, so
"deterministic across two real runs" is unchanged. **Measured: full suite
910s→475s** (foundation 910→475), all 12 green (4,214 tests). Caught and fixed
one self-inflicted red on the way — the +2 new tests drifted README 4,244→
4,246, which dropped `_dimension_sight` to 7 and cascaded; autonomy_loop fixed
it (the documented drift dance), not a logic bug. Cumulative this session:
full gate 1180s→475s (~2.5×), plus `--fast` dev loop 240s (~5×).

**Round 19, 2026-09-05 — test suite sped up + `/next` upgraded (priority 5,
the 12× slowdown was a real defect).** The runner's own comment claimed
foundation was "~90s"; reality was **1083s** — a silent 12× regression, caused
by the foundation suite running the full real-repo `compute_sigil` (which
shells out to run every subsystem suite) from ~4 test paths, each ~226s.
Fixes, all measured, zero coverage lost in the default path:
  - `sigil.py::_dimension_proof` now runs the 8 subsystem suites **concurrently**
    (a real `compute_sigil()` speedup, not just a test trick) — recursion guard
    intact.
  - `test_sigil` computes its determinism pair **concurrently** (452s→~226s).
  - `run_all_tests.sh` runs the 12 suites **in parallel** (wall = slowest
    suite, not the sum) with corrected per-suite timing.
  - New `run_all_tests.sh --fast` (`TITAN_SKIP_REALREPO_SIGIL=1`) skips only the
    heavy real-repo sigil paths for the dev loop — **never** for pre-commit.
  - **Measured: full 910s (was ~1180s), fast 240s (~5× faster dev loop)**, all
    12 suites green (4,212 tests). `.claude/commands/next.md` upgraded: 4–6-agent
    swarm codified, fast/full test modes, team-fit + phone-board + payload
    delivery wired into the end-of-cycle. No README drift (no new tests added).

**Round 18, 2026-09-05 — NZ GETS detail sweep CLOSED (priority 1), 0 cyber
confirmed by category code.** Executed the standing priority-1 item instead of
deferring it. Pulled the live feed (327 notices), filtered cyber by title with
word boundaries (not the "soc"-in-"associated" substring trap) → **0 cyber
notices**. The only real security notices are physical, and their detail pages
(fetched politely, ~6s apart, via `mouth_gets_nz.fetch_tender_detail` —
first RUNTIME-VERIFIED against the live network, previously only unit-tested
with an injected fetcher) prove it by UNSPSC category:
  - 322859 Security Services → 92120000 *Security and personal safety* → pre-qual **None**
  - 324523 Enterprise CCTV → 46170000 *Security surveillance and detection* → pre-qual **None**
  - Corporate Security → 92121700 *Security systems services* → pre-qual **None**
Every one physical guarding/surveillance, none cyber; every one states Required
Pre-qualifications "None" (a stated value, not an inferred absence). This closes
priority 1 with hard evidence and confirms round 14's "0 cyber" with fresh
data. NZ route for the team stays the Government Marketplace (`NZ_MARKETPLACE`).
No new target, no code change — a verified-negative plus a capability advanced
from TESTED to RUNTIME_VERIFIED.

**Round 17, 2026-09-05 — built the winnability scorer (priority 5, unwired
capability closed).** The pipeline had 22 team targets but nothing that told
Kyle *which* his team can win. Built `foundation/team_fit.py`: declare the
team's capability (turnover / insurance / references / languages / 24×7 SOC /
capability tags) and it ranks all 22 MEET / PARTIAL / GAP, naming the exact
blocking clause on every gap. Honest by construction — an undeclared
capability or an unparseable requirement is UNKNOWN (human read), never a
silent pass; hedged "likely/confirm" clauses are UNKNOWN, not hard fails.
Wired into `operator_cli team-fit` (finish the door). It earned its place on
first run: a realistic UK-only MDR team scores 3 MEET (RTÉ/HSE/ECHA DPS
frameworks) / 14 PARTIAL / 5 GAP — and it flagged that Statens IT DK (my
standing "bid first" rec) carries a Danish-market-presence clause, so it's
PARTIAL (confirm a DK partner), not a clean bid, for an English-only team. The
German (degewo, Frankfurt), Dutch (Radboud) and DK targets GAP out without a
local-language team member — a real, previously-implicit wall now made
explicit. 25 tests green; README 4,219→4,244; no new external notice this
cycle.

**Round 16, 2026-09-05 — tried to pull the Irish SOC award/scoring criteria,
documents are browser-gated (priority 2).** Attempted to add bid-winning
intelligence (the scoring method, not just pass/fail) for the top Irish SOC
target (HSA, rid 8939732). Its eTenders notice page loads (200, 31KB) but the
document-download links are **JavaScript-rendered** — 0 `documentId`s in the
static HTML, 34 `javascript` references, no `downloadContractDocument` link.
So the full tender documents (with the award/scoring criteria) are
browser-only for an automated agent; the pass/fail selection requirements the
board extracted earlier via the anonymous-download flow are the
machine-extractable set, and they are already in `team_targets.py`. The team
opens the direct notice link in a browser to download the full pack. Verified
negative — no new extractable intelligence.

**Round 15, 2026-09-05 — suspected defect investigated, DISPROVEN (priority
5).** Last cycle's deep_sweep reported "600 security-relevant rows" and my
ad-hoc probes kept catching "soc" inside social/associated, so I checked the
production filter for a substring bug. Clean on both counts: `mouth_etenders_
ie.is_security_relevant` uses `"soc "` **with a trailing space** (matches the
standalone word, never "so**c**ial"), and `deep_sweep` returns **all** walked
register rows by design (deduped on `key`) — it does not pre-filter, so "600"
was 60 pages × 10 rows, not 600 security matches. My own prior label was
wrong; the code is correct. No change needed. (The "soc"-substring looseness
was only in my throwaway probe scripts, never the repo.) Recorded so it isn't
re-suspected.

**Round 14, 2026-09-05 — NZ GETS swept for the team, 0 cyber.** Priority 1 for
the team dimension: pulled the live NZ GETS feed (327 open notices), filtered
for cyber/security-services. **Zero genuine cyber tenders** — every keyword
hit was a false positive on "soc" inside "so**c**ial"/"asso**c**iated"
(Professional Learning, Forestry, Bike Hub...). The NZ route stays the
Government Marketplace, already held as `NZ_MARKETPLACE`. With NZ now checked,
**all five reachable sources (UK / Ireland / TED-EU / Denmark / NZ) are
confirmed exhausted for the team** — the 22-target pipeline is the complete
reachable set. The genuine remaining levers are Kyle's: the team bidding the
live queue, and the team's capabilities (references/insurance/languages) so
the 22 can be ranked and drafted.

**Round 13, 2026-09-05 — fresh TED re-sweep, 0 new cyber.** TED posts daily,
so re-pulled the cyber set (223 matched): **no new team-viable cyber contract**
since the last sweep. The 8 in the 400k–30M future-deadline band are the same
broad-IT/non-cyber ones already assessed — incl. Irish Rail 605566 (€4M, 14
Oct), which I fetched in full this time and confirmed is a **passenger-
information Station Services Mediation System, NOT cyber**. With UK, Ireland,
TED-EU and Denmark all now mined, the hunt is saturated across every reachable
source; the pipeline of 22 targets is the complete reachable set. Recorded so
the identical sweep isn't re-run expecting a different answer.

**Round 12, 2026-09-05 — deep Ireland walked for the TEAM, exhausted.**
Priority 3, redone for a team (not just solo cyber-DPS): `deep_sweep`
walked **60 register pages (600 security-relevant rows)** and found **zero
new genuine cyber tenders** beyond the 5 dated + 9 DPS already held. The
handful that keyword-matched were false positives (social-housing
construction, a hybrid bus, PR/comms, LAN/WAN maintenance — several with
2024 deadlines already passed). The Irish cyber seam is complete for the
team, same conclusion as it reached for the solo operator. Recorded so a
future cycle doesn't re-walk it.

**Round 11, 2026-09-05 — all 5 dated Irish tenders now have DIRECT links +
verified live ⭐.** Walked the eTenders register (19 pages) and found all five
with their `resourceId` notice links, confirmed still in the current register
with exact deadline times: **Fáilte 24 Sep 12:00** (rid 8915449), **Oireachtas
28 Sep 12:00** (8943772, "Managed [Security]"), **An Post 29 Sep 12:00**
(8927838, "Security Operations Centre"), **Dept of Justice 2 Oct 12:00**
(8916237, "Managed Services PQQ"), **HSA 12 Oct 17:00** (8939732, "Security
Operations Centre (SOC)"). Team entries switched from the eTenders base URL to
the direct `prepareViewCfTWS.do?resourceId=` links — the team clicks straight
to each notice. (Aside: my first register-walk attempt printed `resourceId`
None — that was a wrong field name in my own probe, `resource_id` is the field;
the parser was never broken.)

**Round 10, 2026-09-05 — clock live; freshness + a real timeout fix.** The
date rolled to 5 Sep, so re-verified the near-deadline UK targets: **all
still active** — Southern Water £10M MDR (closes 21 Sep 16:00), T160/NI Water
(active, submission imminent), Bradford (closes 14 Sep 16:00), Jisc (active,
enquiries close 21 Sep). Nothing expired. **Defect found and fixed:**
`mouth_common.DEFAULT_TIMEOUT_SECONDS` was **10s**, but the UK Find a Tender
OCDS API (the path `fat-notice` uses to verify contracts) is responding in
**33–48s** today — so every UK verification was failing on a merely-slow, not
down, host. Raised to **45s** (safe: MAX_FEED_BYTES still bounds the response;
the timeout only bounds a stalled read). The host is exceptionally slow right
now (48s), recorded as a transient — the earlier 45s checks this cycle
succeeded, which is how the statuses above were confirmed.

**Round 9, 2026-09-04 — fresh UK re-sweep + Irish dated access check.** TED
Ireland returned 0 for the dated tenders (they're on eTenders, below TED
threshold; the board has no direct resourceIds so eTenders search-by-reference
stays the access path). Re-swept the UK cyber CPVs (feed is dynamic): **no new
BIDDABLE contract** — the 5 not-already-held were IT-infra, an investigation
system, and 3 pre-tender PME/RFI notices. The PMEs are a real **pipeline
signal** though: more UK managed-security tenders are coming. Added the most
concrete as a watch — **WMCA (West Midlands Combined Authority) — Managed SOC,
£540k, planning stage**: respond to the market engagement now to be positioned
when it opens. `team_targets.py` now 22 (21 real + 2 UK pipeline watches).

**Round 8, 2026-09-04 — freshness on the near-deadline TED targets.** Re-queried
TED by publication-number: **all three still LIVE**, with exact cutoff TIMES
now captured — **Statens IT (DK) MDR DKK 24M closes 17 Sep 12:00**, **degewo
(DE) €691k closes 22 Sep 10:00**, **Fáilte (IE) €800k closes 24 Sep 12:00**.
Updated the entries so the team has the exact deadline hour, not just the day.
The TED notice-detail URL is the access point for these (TED doesn't expose
the buyer's document portal the way UK OCDS did). No stale/closed targets.

**Round 7, 2026-09-04 — bid paths for the top UK targets (drive to the submit
line).** Instead of another target, pulled the FULL OCDS releases for the 3
UK flagship contracts and gave the team the real access path for each — buyer,
free document portal, human notice URL, confirmed deadline:

- **UK MDR £10M** = **Southern Water Services**, docs FREE/unrestricted at
  `southernwater.bravosolution.co.uk`, notice `/Notice/076524-2026`, **closes
  21 Sep 16:00**.
- **Jisc SIEM/SOAR £11.1M** = JISC, docs at `uk.eu-supply.com` (JISC), notice
  `/Notice/083054-2026`, enquiries close 21 Sep.
- **T160 Cyber Assurance £720k** = **Northern Ireland Water**, docs at
  `etendersni.gov.uk`, notice `/Notice/074300-2026`, submission imminent.

**Pattern worth carrying:** the UK cyber MDR/SIEM buyers are UTILITIES and
EDUCATION (Southern Water, NI Water, JISC), not central government — a good
seam for future UK hunts. The team can now go straight to the documents.

**Round 6, 2026-09-04 — hunt saturating, two English sources checked.** TED
Ireland cyber (CY=IRL): **0 new** beyond the 5 dated + Fáilte already held.
Tried two more English-language portals: **Public Contracts Scotland is
robots-blocked** (`User-agent: * / Disallow: /` — only named search engines
allowed; recorded as a finding, not fetched). **Sell2Wales is reachable but
an ASP.NET form-POST search** (ViewState-stateful) — a fragile bespoke
scraper for a small nation with few cyber contracts; **deferred as low-ROI**
given the team already holds 21 targets, more than it can bid. Honest state:
the readily-reachable English + EU cyber sources (TED, UK Find a Tender) are
mined; further cycles yield diminishing NEW targets. The value now is the
team acting on the 21 — which needs Kyle's team capabilities to prioritise
and prep. (Building the Wales scraper is a standing option if Kyle wants that
source; it is not worth an autonomous cycle unweighted.)

**Round 5, 2026-09-04.** Swept 6 more UK cyber-adjacent CPVs (72810000,
48731000, 72220000, 79417000, ...) — matches were generic audit/investigation,
**no new genuine cyber contract** (verified negative, recorded so they're not
re-swept). Pulled the enquiry periods for the two UK targets whose submission
deadline OCDS didn't carry: **T160 enquiries CLOSED 2 Sep → submission
imminent, bid urgently**; **Jisc enquiries close 21 Sep → submission soon
after**. Both updated in `team_targets.py`.

**TEAM-SCALE hunt — UK cyber via IT CPVs, 2026-09-04 (round 4) ⭐.** Acted on
last cycle's finding (UK cyber lives under IT CPVs, not 79700000). Swept Find
a Tender CPVs 72000000/72500000/72600000/48730000/72212731 → **11 genuine UK
cyber-title notices**, verified the live ones via OCDS. **Three active,
English-language, high-value contracts added — the best team fit yet (no
translator needed):**

- **UK — Managed Detection and Response Tender, £10,000,000, status active,
  closes 2026-09-21** (OCDS-verified) — now the #2 dated target.
- **Jisc — SIEM/SOAR for its Security Operations Centre, £11,100,000, active.**
- **T160 — Cyber Assurance Services, £720,000, active.**

(SOC/SIEM 06a22d was `planned` not open — noted, not added; Bradford 06e59c
already on the board.) English is the strongest jurisdiction for the team, so
these outrank the German/Dutch/Danish ones on fit. `team_targets.py` now 21.

**TEAM-SCALE hunt — TED round 3, 2026-09-04.** UK keyword search proved a
dead end (the `keywords=` param is silently ignored — returns generic
notices; CPV filtering is the only UK lever, and cyber has no single CPV).
Went back to TED (structured values work) and reviewed the remaining
cyber-matched notices. Most matched a security keyword but aren't cyber
(a comms platform, a grant-management system, office automation) — not
added. **Two are genuinely cyber and verified, added:**
**Universitätsklinikum Frankfurt (DE) — Cybersecurity Managed Service,
€7,926,450, closes 6 Oct** (German-language) and **Radboud University (NL)
— security governance/risk/ISO compliance, €10,800,000, a long framework to
2034** (Dutch). `team_targets.py` now **18**. Discipline held: broad
IT-with-a-cyber-mention frameworks (DG SANTE €7M, Clean Hydrogen €15M,
ECDC €12M) were seen but NOT added — they're IT infrastructure, not cyber
delivery, and inflating the list helps no one.

**TEAM-SCALE hunt — UK, 2026-09-04 (round 2).** Pulled UK Find a Tender's
security-CPV feed (79700000, 20 notices). **Finding worth carrying: that CPV
is mostly PHYSICAL security** (guards, CCTV, body cameras, alarms, lone-worker
devices) — UK *cyber* tenders sit under IT CPVs (72xxxxx), so future UK cyber
sweeps should query those, not 79700000. One genuine cyber contract in the
feed: **UKRI-6251 — Cyber Security Managed Service / MDR / SOC, £1,500,000**
(UK Research & Innovation), verified via its OCDS release — **status
`planning`**, i.e. buyer intent published but the tender is NOT yet open.
Added as a team target flagged PLANNING/watch (prepare + register interest,
don't bid yet). English-language, no jurisdiction barrier for a UK-facing
team. `foundation/team_targets.py` now 16 targets.

**TEAM-SCALE hunt, 2026-09-04.** Now that Kyle is building a team (credential
walls no longer disqualify), the INSUFFICIENT_DATA tender notices are real
leads. Pulled TED's structured cyber notices (223 items, values attached):
**87 carry a value ≥ €500k; 24 are genuinely-cyber, team-viable
(€300k–€40M) with a future deadline.** Added two verified new team targets
(`foundation/team_targets.py`): **Statens IT (DK) Managed Detection &
Response, DKK 24M, closes 17 Sep** and **Danmarks Nationalbank (DK)
cybersecurity advisory, DKK 9.2M, closes 2 Oct**. The live pull also **caught
an error**: `IE_FAILTE`'s value was the turnover *requirement* (€400k), not
the €800k contract value TED shows — corrected; `IE_OIREACHTAS`/`IE_ANPOST`
values relabelled as turnover bars (contract value UNKNOWN), degewo confirmed
live at €691,200 / 22 Sep. Bigger mega-frameworks seen but not added (€700M
EC, €162M Consip — consortium-scale, not this team yet).

**Priority-4 dynamic re-sweep, 2026-09-04 — clean.** Bounty board: 63
programs, **0 new**, Ant Group still the top uncontested target. Tender
hunt (date-bounded, last 10 days across TED/UK/IE/NZ/DK/NL): 385 fetched,
28 assessed, **QUALIFIED=0** (26 INSUFFICIENT_DATA, 2 DISQUALIFIED) — the
standing pattern (criteria live in the procurement documents, not the
notices). Nothing new actionable for a SOLO operator; team-scale is above.

**Deliverable integrity check, 2026-09-04.** All **17 roster links
re-fetched live** — every one resolves (15× HTTP 200, Bradford a normal
302 redirect, NSW `buy.nsw.gov.au` + QITC `hpw.qld.gov.au` a WAF 403 that a
human browser passes). **Zero genuinely broken links.** Bounty board
re-swept: 0 new, Ant Group still the top uncontested target. Close pack
re-checked: Synack and Immunefi render with accurate walls/needs. A new
offline test now guards link well-formedness so a typo'd link in a future
card can't ship. Nothing broken, nothing new — recorded so the "all clean"
state is on the record, not assumed.

**Roster freshness re-verification, 2026-09-03.** The two time-critical
digest cards were re-fetched live to be sure the money-printer isn't
showing a stale deadline: **Bradford £300,327** — still `active`, closes
**2026-09-14T16:00Z** unchanged, OCDS release states no entry gate
(re-read via the fat-notice OCDS path). **NLnet NGI Zero** — call page
live, **deadline November 3, 2026** confirmed, "available to individuals"
present. Both accurate; no change needed. Also checked **Pulse Security**
(§13 associate-tester lead): reachable (robots `Disallow:` empty) but its
careers page shows **no active opening** — so per "absence is UNKNOWN" it
stays a lead, not promoted to the roster (cold-approaching a firm with no
posted role is speculative, not a verified opportunity).

**Operator profile this board is scored against:** solo trader, Cairns
QLD, has an ABN, **no certifications** (no OSCP/CREST/GIAC/CISSP), **no
professional indemnity or public liability insurance**, **no corporate
reference contracts**, no employees, English only. Australia is a WTO
GPA party (since 5 May 2019), so nationality is not a barrier anywhere
below.

---

## 📱 NEW 2026-09-04 — THE PHONE MONEY-PRINTER (so you never open the PC)

Every opportunity on this board is now delivered to your phone as
individual, value-first, tappable cards — most-winnable first — at the end
of every run. Built this cycle:

- `foundation/ops_digest.py` — the 15 live opportunities as structured
  cards (value, gate, deadline, exact steps, source), ranked 🟢 DO NOW →
  🟠 ACT SOON → 🔵 PURSUE → 🟡 UNVERIFIED → ⚪ WATCH. Ruled-out items (the
  8 reference/insurance walls) are excluded, not sold.
- `foundation/telegram_notify.py` — pushes the digest to **your own
  Telegram** via **your own bot token**, gated on a new `NOTIFY_OPERATOR`
  scope. Runs now in dry-run; sends live the moment you set the token.
- A phone dashboard (Artifact) + the digest are sent to your phone through
  the Claude app already — no token needed for that.
- Wired into `next.md`: every future run ends by regenerating and sending
  the digest. 27 new tests, token-never-leaks pinned.

**Your one step to turn on Telegram:** message @BotFather → `/newbot` →
paste the token per `HUMAN_DECISIONS.md`. Until then the phone dashboard
covers it.

**2026-09-03 — the "ruled out" count is now real, and the eliminated set is
SHOWN not hidden.** The digest hardcoded "8 ruled out" in two places while
the true count was **12**. Replaced the magic number with a `RULED_OUT`
registry (`ops_digest.py`): each eliminated opportunity carries the exact
clause that ruled it out (RTÉ's held €6.5M/€1M/€1M insurance, the HSE
24×7-staff-in-Ireland geography wall, the five dated Irish notices'
turnover+insurance+reference bars, PNG's PGK5,000 paper-only fee, TED
degewo/ECHA, NHS's prior-DPS-admission gate). The count is derived, and the
phone dashboard now has a "❌ Ruled out (12) — shown so you can challenge
them" section at the bottom. **This is deliberate: a wall that changes (new
insurance, a partner's turnover, a consortium) moves an item back into
play, so the eliminated set must be visible, not buried.** 5 tests pin it.

**2026-09-03 — the digest can no longer lie about a closed deadline.** The
one way the money-printer could actively mislead you was showing an expired
tender as 🟢 DO NOW after its date passed. Added deadline-parsing +
auto-expiry to `ops_digest.py`: any card whose closing date is in the past
is downgraded to ⏱ CLOSED, drops its action steps, and sinks to the bottom
— computed against the run date, fail-safe (an unparseable/standing
deadline never expires, so a live item can never be hidden by mistake).
Verified: at a 2027 date Bradford + NLnet correctly flip to CLOSED and the
live count drops from 15 to 13. 8 new tests.

**Priority-4 re-sweep 2026-09-03: still quiet.** Live YesWeHack + HN board,
63 programs, **0 new**. Ant Group still UNCONTESTED (0 reports), same
distribution as prior cycles. Roster unchanged, verified accurate — no new
opportunity to add.

**2026-09-03 — the digest is now ONE command.**
`python3 -m foundation.operator_cli digest` regenerates the phone
dashboard, dry-runs/sends the Telegram push, and prints the top DO-NOW
moves — the end-of-run step `next.md` mandates, previously a remembered
sequence. Sonnet-viable, tested (2 tests), offline without a token.

**2026-09-03 — Denmark/NL RESOLVED to human-browser-only (was "read one
document").** The board flagged the Danish notices as unread. This cycle:
- `udbud.dk` serves its notice pages as a **902-byte JavaScript SPA shell**
  ("this page doesn't work properly without JavaScript enabled") — no
  criteria server-side. robots.txt permits `/bekendtgoerelse/`, so this is
  an architecture block, not a robots block, and not worked around.
- The sanctioned structured route (TED, `operator_cli hunt --ted-query
  'FT ~ ("cyber") AND CY=DNK' --live`) returned **QUALIFIED=0** across 45
  assessed notices (INSUFFICIENT_DATA=35, DISQUALIFIED=10) — every Danish
  cyber notice withholds its selection criteria from the notice itself, the
  same standing pattern as the other EU national boards.
- **Conclusion:** neither Denmark nor Netherlands can yield a QUALIFIED
  lead by honest automated reading — the criteria live in login/portal-
  gated documents. A human browser is the only route. Recorded so a future
  cycle doesn't re-run the identical query expecting different output. This
  seam is mined for the automated agent.

---

## TIER 1 — open today, no credential gate, no deadline

These need nothing you do not already have. None has a closing date,
which is exactly why they are the ones that quietly never get done.

### 1. ZDI (Zero Day Initiative) — pays cash for vulnerabilities, year-round

| | |
|---|---|
| **Value** | Per-vulnerability. Range varies by target class; see their published table |
| **Gate** | None. Open globally to individuals |
| **Excluded countries** | Cuba, Iran, North Korea, Sudan, Syria. **Australia is not excluded** |
| **Deadline** | None — standing market |
| **Cost to enter** | Free |
| **URL** | zerodayinitiative.com |

The purest capability-for-cash market found in this entire campaign. No
company, no licence, no insurance, no references, no interview.

**It is also the prerequisite for the big prizes** — see Pwn2Own Ireland
below, which requires $15,000 already earned through ZDI.

**ACTION:** register a researcher account. Free, no deadline, no risk.

**UNKNOWN:** the non-US tax form for payouts is not stated on their FAQ
(only W-9 for US taxpayers is confirmed). Ask them at signup.

---

### 2. Ant Group — zero reports, three wildcard domains

Swept YesWeHack's **entire public board** — all 60 active programs —
sorted by report count ascending, 2026-09-03. The distribution is not
close:

```
reports  min   max    program
      0   $10  $2500  Ant Group Security Response Center
     15    $8  $5000  Tencent
    106  $200  $1000  DataDome        <- the cliff
    118   $50  $2000  Dossier Medical Partage
    ... 56 more, all 106+
```

**Two programs out of sixty are under-contested.** Everything else has
been picked over by 106 to 900+ reports.

**Ant Group's scope, read from the program's own record:**

```
[wildcard]        *.alipayplus.com
[wildcard]        *.antom.com
[wildcard]        *.worldfirst.com
[web-application] bettrfinancing.com
[web-application] anext.com.sg
[web-application] alipayhk.com
[web-application] antbank.hk
[other]           any other application listed at security-en.alipay.com
```

**Three wildcards means every subdomain is in play — and nobody has
filed a single report against any of it.** Eight scopes, zero reports.

**✅ RE-VERIFIED LIVE 2026-09-05 against the program's own API.** Still
`reports_count: 0`, `bounty: true`, `disabled: false`, $10–$2,500, and
the scope above is byte-for-byte unchanged. **Zero reports after two-plus
weeks is the proof this is genuinely unlooked-at, not a stale snapshot** —
if it were merely new, someone among YesWeHack's hunters would have filed
by now. It remains the single most winnable target on this board.

Re-scanned the full public board the same day for any *newer*
low-contested programme: still exactly two under 20 reports (Ant Group 0,
Tencent 15), nothing new appeared, one programme dropped off (60 → 59).
Kyle is not missing a fresher target — Ant Group is still the one.

| | |
|---|---|
| Minimum bounty | **$10** — so it pays for a Low, which is the finding a newcomer actually gets first |
| Maximum | $2,500 |
| Report submission cost | 0 |
| Sector | Finance / Assurance |
| Average first response | 0 (no reports yet to respond to) |

**Tencent** is the only other one: 15 reports, minimum **$8**, maximum
$5,000, scope split into Core and Non-Core product lists published at
`en.security.tencent.com`.

**Why report count beats payout size here.** A program with a $15,000
ceiling and 900 reports has had every accessible finding taken. A $2,500
ceiling with zero reports has not been looked at. For someone with no
reputation, the odds of *any* payout dominate the size of it — and this
is the only place on that board where the odds are good.

**ACTION:** register on YesWeHack, read Ant Group's full brief and scope
rules, and work the wildcards. Nothing has been tested and nothing will
be — testing outside an authorised scope is illegal regardless of intent,
so read the brief first and stay inside it.

---

### 2c. Immunefi — crypto bounties, the most CREDENTIAL-open route found ⭐ NEW 2026-09-03

Swept live 2026-09-03: `immunefi.com/bug-bounty/` (robots.txt `Allow: /`,
program data server-embedded, no evasion). **183 live programs parsed
directly from the page.** The structural finding is real and it is unique
on this board:

```
183  live programs
 76  require NO KYC (no identity verification at all)
$1,000 – $10,000,000  max-bounty range
```

**Top no-KYC ceilings (no identity docs required):**

| Max bounty | Program |
|---|---|
| **$10,000,000** | Sky |
| $5,000,000 | SparkLend · GMX |
| $3,333,333 | Olympus |
| $2,000,000 | Lido · Gnosis Chain · rhino.fi |
| $1,000,000 | Balancer, PancakeSwap, CoW, Origin, Beanstalk, + more |

**Why this is its own category.** Every credential wall that killed the
Irish and NSW routes — references, insurance, turnover, certifications,
a company — is **absent here**, and on 76 programs even KYC is absent.
This is the single most credential-open income source the campaign has
found. Nothing about Kyle's lack of insurance, references or certs
matters at all.

**The honest counterweight, and it is the whole story.** These are
**smart-contract / DeFi security audits** — Solidity, protocol logic,
economic exploits. A $10M payout means finding a critical bug in code
that specialist auditors have already been over. **Kyle's smart-contract
skill is UNKNOWN** (the operator profile declares no skills), so this is
recorded **UNVERIFIED, not QUALIFIED** — the gate here is *capability*,
not credentials, and it is a high one. Per "UNKNOWN is never ZERO" it is
not assumed he lacks the skill either; whether it fits is his call.

This is the exact opposite tradeoff from Ant Group (item 2): Ant Group is
low-skill, low-payout, uncontested; Immunefi is high-skill, high-payout,
heavily-contested. Both are now on the roster; Immunefi sits at UNVERIFIED
so it never outranks a route Kyle can act on today.

Added to the digest roster and close pack this cycle.

---

#### Bounty-platform reachability mapped — 2026-09-03 (D-015)

Checked whether the other major bounty platforms can be swept like
YesWeHack and Immunefi. **They cannot, and it's recorded so no future
cycle re-probes them.** HackerOne (`/directory/programs` → 1.8 KB JS
shell), Bugcrowd (`/engagements` → marketing shell, no embedded records)
and Intigriti (login-gated app SPA) all render their directories
client-side. robots.txt permits all three — the block is architectural,
not a robots wall, and their private GraphQL endpoints were **not**
reverse-engineered (same discipline as udbud.dk / ADB). **Automatable
bounty coverage = YesWeHack + Immunefi; the other three are a
human-browser step, not a wall.** Bounty board re-swept same day: quiet,
Ant Group still the top uncontested target; the one `new` signal was an
HN full-time job, not a bounty. See `docs/DECISIONS/D-015`.

---

### 2b. The two bounties whose target is PUBLISHED SOURCE CODE ⭐

Swept live 2026-09-04: 64 opportunities across YesWeHack (60 programs)
and Hacker News "Who is hiring?" (4). Two of the 60 are a **different
shape from every other item on this board**, and the difference is the
scope field, read from the platform's own API:

| Program | Scope, verbatim from the API | Bounty | Reports filed |
|---|---|---|---|
| **Swiss Post — E-Voting** | `Source Code`, `System Specification`, `Protocol of the Swiss Post Voting System`, `Scenarios with Special Bounties` | **€100 – €230,000** | 1,855 |
| **Dovecot** (IMAP server) | `Dovecot IMAP Server and Pigeonhole SIEVE` — `scope_type: open-source` | €100 – €5,000 | 356 |

**Why this is its own category.** Every other program on that board asks
you to test somebody's *running production system* — which means rate
limits, WAFs, scope boundaries you can cross by accident, and a legal
position that depends entirely on staying inside a brief. These two ask
you to read **published source code and published specifications**. The
artifact is downloadable, re-readable, and yours to study for as long as
you like. Nothing is touched. Nothing can be knocked over.

Swiss Post's e-voting source is published for public scrutiny by design
— that is the point of the programme — and it carries the **largest
single payout figure found anywhere in this campaign**, with named
special-bounty scenarios above the base range.

**The honest counterweight, and it is heavy:** 1,855 reports on Swiss
Post and 356 on Dovecot. Both are thoroughly worked. That is the
opposite of the Ant Group logic (0 reports) that put Ant at Tier 1 —
here the argument is not "nobody has looked", it is "the target rewards
depth rather than speed, and it can be studied offline for weeks without
touching anything". Those are different bets. Both are on the board.

**The single gate on all 64, and it is one-time:** a free YesWeHack
account. One registration opens every program above and every program
found in future sweeps. Nothing after it needs the operator again.

**✅ NOW RANKED BY THE NEWCOMER'S EDGE — 2026-09-05.**
`python3 -m foundation.operator_cli income --live` now surfaces each
program's **report count** — the single most decisive signal for a solo
operator with no reputation — and sorts the listing **least-contested
first**. A program with 900 reports has had every accessible finding
taken; one with 0 has not been looked at. `income_watch` was dropping
the count entirely. Live result, top of the list:

```
Ant Group Security Response Center   payout=10-2500 USD   UNCONTESTED (0 reports)  scopes=8
Tencent Bug Bounty Program           payout=8-5000 USD    reports=15               scopes=2
DataDome Bot Bounty                  payout=200-1000 EUR  reports=106  <- cliff    scopes=6
```

**The newcomer's-edge triple is now complete (2026-09-05):** *uncontested
× low payout floor × broad scope.* The third signal — **scope breadth**,
the count of scopes a program admits (attack surface) — was also being
dropped by `income_watch`; now surfaced and used as the secondary sort
(more scopes first within a contested level). It confirms why Ant Group
dominates: **0 reports AND 8 scopes** (three of them wildcards —
`*.alipayplus.com`, `*.antom.com`, `*.worldfirst.com`) AND a $10 floor
that pays for a Low finding. Contested still dominates — a wide-scope
busy program never outranks a narrow-scope fresh one.

Two of 63 are under-contested; everything else is past a 100+ report
cliff. This is the ONE income route that needs no insurance, no
references, no turnover — and it now tells you exactly which programs a
first finding is winnable on. UNKNOWN counts (a hiring gig has no such
concept) sort after the known ones, never treated as zero.

#### ✅ THE CORPUS IS ON DISK — and the cheap surface is already clean

**Kyle ran the clone 2026-09-04.** 485 MB at
`~/titanos_launch/titanos-next/e-voting-documentation`, release 1.8.0.5:
129 PDFs, 241 markdown files, the full Protocol, the Symbolic-models
(ProVerif), every past examination report, and the Trusted-Build
checksums.

**First and most important thing read — the programme's own rules:**

> "You can analyse our artefacts by completing: **a static test of
> documentation and source code**"

Documentation defects are explicitly in scope, and explicitly a Low
severity category ("typos in the GitLab Markdowns or in documents").
That is a real entry path requiring nothing but careful reading.

**Then the systematic pass, and the honest result: nothing.**

Cross-referenced the System Specification (v1.6.1, 166 pages, 78
numbered algorithms) and the Verifier Specification (v1.7.1, 48 pages,
44 numbered verifications) against themselves and each other. Five
candidate defects were raised. **All five were disproven.**

| Candidate | What it actually was |
|---|---|
| `Algorithm 6.7` referenced, never defined | **My own bug.** The PDF encodes "fi" as ligature U+FB01, so `ConﬁrmVoteAgreement` truncated to `Con` and the definition vanished |
| `ExtractVeri` defined at two numbers | Same ligature — two different names truncated to a shared prefix |
| Verification numbers 4.xx and 9.xx missing | The changelog records verifications **removed and merged** across versions without renumbering |
| `Verification 0.01` in neither run | `ManualChecksByAuditors` — explicitly "the checks that the auditors must perform **manually**", deliberately outside both automated runs |
| 27 algorithms never cited | All 27 cited **by name** rather than by number. `MixDecOnline` appears 26 times; its number never does |

Final state: **78 definitions, 78 resolved, zero dangling references,
zero duplicate numbers, zero duplicate names, zero orphans.**

**This is worth more than it sounds.** A programme with 1,855 filed
reports has been read very carefully by very good people. Confirming
that the cheap structural checks are exhausted tells you where *not* to
spend the next hundred hours. The remaining value is in depth — the
cryptographic protocol, the ProVerif symbolic models, the implementation
— not in document consistency.

**And two of the five candidates were manufactured by my own text
extraction**, which is the same failure this board has now recorded four
times in two days: confident output computed over noise. Ligature
normalisation is now enforced in code, not remembered.

`foundation/spec_crossref.py` makes the whole pass repeatable, and it
emits `CrossRefCandidate` — never `Finding`. A candidate cannot even be
constructed without stating why it might be innocent, because all five
were.

**Where the guarantees actually stop — read this before any depth work.**
The formal results, from the repository's own output files:

- **Vote privacy: fully proven.** `RESULT Diff-equivalence is true` for
  both the CCM1 and CCM2-3-4 models.
- **Individual and universal verifiability: the correspondence queries
  are `true`.** The reachability sanity checks come back
  `cannot be proved` in the full models and are established in separate
  reduced ones — which the README's own "Abstractions / Limitations"
  section documents as deliberate methodology. (Sixth candidate, also
  disproven.)
- One model is named `...-Haines-attack.pv` and its correspondence query
  returns **`is false`** — that is a *modelled known attack*, published
  by Swiss Post themselves, not an open hole.

And the protocol states its own three trust assumptions plainly:

1. **Polynomially-bounded adversary** — a fault-tolerant quantum
   computer breaks the underlying assumptions. Named as future work.
2. **The voting client is not attacker-controlled** *for vote secrecy*.
   Individual verifiability survives a malicious client; secrecy does
   not. "We cannot use cryptography to prevent attackers from spying on
   the voter's choices on malicious clients."
3. **The setup component is trustworthy.** Explicitly a single point:
   "one cannot expect the voter to combine different code sheets by
   hand, and the costs of printing multiple code sheets in independent
   printing facilities would be currently prohibitive."

Plus one flagged weak spot in the *foundations*: privacy rests on the
**Subgroup Generated by Small Primes (SGSP)** problem, which Swiss Post
itself notes "has been studied less in the academic literature than
DDH". They commissioned a CNRS/LORIA expert to write on it —
`Protocol/sgsp.pdf`, 314 KB, and it is on disk.

**That is the map.** Assumptions 2 and 3 and the SGSP hardness question
are where a genuine finding would have to live, because everything
inside the model is already proven.

#### 🔴 STRATEGY CORRECTION — reading the specs was the wrong plan

**Read the 2026 Public Intrusion Test final report, on disk, added to
the repo 2026-08-26.** It is the record of what everyone else found, and
it says the money is not where I have been looking.

**The 2026 PIT, in numbers:**

| | |
|---|---|
| Window | **6–24 July 2026** — three weeks, once a year |
| Participants | 38 hunters submitted; 5,479 distinct IPs from 107 countries; 403,000+ requests |
| Reports | **85** |
| Confirmed | **6** — 1 High, 1 Medium, 4 Low |
| Rejected | 46 Informative, 23 duplicates, 10 out of scope |
| Acceptance rate | **7%** · duplicate rate **27%** |

**What the confirmed High actually was, and what it paid:**

> "Cache Poisoning in Encryption Group Handling Causes Voting Server
> Availability Impact" — requests to `sendVote`/`confirmVote` instantiate
> new encryption-group cache entries **before authentication completes**;
> the cache is keyed only by `p`, so an attacker can poison it with a
> different generator `g`. **Reward 19,000 €.**

The Medium was a missing context validation in `sendVote` letting a
voter specify another voter's `verificationCardId`.

**Both are implementation bugs in the voting server. Neither is a
cryptographic or specification flaw.** That is the whole correction.
Every hour I spent cross-referencing the System Specification confirmed
what this report already implies: the spec surface is clean, and the
findings that pay come from *running the software*.

Note also: the High paid **€19,000**, not the €50,000 ceiling. And
`Release 1.6.1` — the exact System Specification version I analysed —
**is the release that fixed it.** I was reading the post-fix document.

**Two reward schemes, not one, and the board previously conflated them:**
YesWeHack lists the year-round programme at **€100–230,000**. The PIT
report states **"rewards of up to 50,000 € per confirmed finding"** plus
**"an extra bounty of 3,000 € for each of the first three confirmed
findings"**. Whether the €230,000 is a distinct year-round ceiling or the
same scheme described differently is **UNKNOWN** — both figures are
quoted here with their sources rather than reconciled by guess.

**The access structure is the real finding.**

- **Standard PIT: no registration required to test.** Registration is
  needed only to submit for a reward. Genuinely open.
- **PIT+ is invitation-only.** 2026 was its first edition: **100+ applied,
  20 selected.**
- **Both the High and the Medium originated in PIT+**, where perimeter
  protections were deliberately relaxed for deeper analysis — then
  reproduced in the standard PIT as the rules require.

So the valuable findings came from the restricted tier of 20, not the
open tier of 5,479 IPs.

**And the genuinely ungated route, from `REPORTING.md`:**

> "You can analyse our artefacts by completing: … **dynamically testing a
> self-deployed and running instance of our system**"

The source is published and self-deployment is explicitly in scope. That
means the implementation — where both 2026 findings actually were — can
be tested **on Kyle's own machine, year-round, touching nobody's
infrastructure, needing no permission and no invitation.** That is the
first route on this board that is both where the money is and free of
any gate.

**Revised plan for this target:**
1. Stop reading specifications. Proven exhausted over two cycles.
2. Clone `e-voting/e-voting`, follow `BUILDING.md`, run it locally.
3. Hunt implementation bugs of the 2026 shape — pre-authentication
   resource allocation, cache keying, missing cross-entity validation.
4. Register interest in **PIT+ 2027** when it opens. 20 places, 100+
   applicants, and it is where the paying findings came from.

This intelligence is now a computed capability, not a one-off read:
`python3 -m foundation.operator_cli pit <report.pdf>` reads any PIT
final report for acceptance rate, duplicate rate and what each confirmed
finding paid. Built because `mouth_bounty`/`income_watch` answer "does
this programme exist" but never "is there anything left in it". Honest
limitation stated in the module: the extraction is tuned to the 2026
report's phrasing; the 2022–2025 reports use different prose ("received
four reports") and return all-UNKNOWN rather than wrong numbers — the
correct failure direction.

#### 📝 ONE SUBMITTABLE CANDIDATE — Low severity, documentation

**✅ NOW WRITTEN UP AS A READY-TO-FILE REPORT — 2026-09-03.** The campaign's
one real finding was documented here but never turned into a report Kyle
could actually submit — a finish-the-door gap. `SGSP_SUBMISSION_DRAFT.md`
is that report: title, severity, summary, the three-source evidence table,
suggested one-line remediation, reproduction command, and an explicit
disclaimer that it is a documentation finding and must be filed as Low, not
as a vulnerability. The moment Kyle registers on YesWeHack (a DO-NOW card),
he can review and file it. Drawn strictly from the verified evidence below;
nothing added.

**Read `Protocol/sgsp.pdf` (Pierrick Gaudry, CNRS/LORIA, May 2022).**
It is 10,000 characters and it contains one claim about the *system*
rather than the mathematics:

> "**Fact.** It is crucial to have a 'provably randomly generated'
> prime. In the Swiss Post case, it means that the seed given to
> Algorithm `GetEncryptionParameters` must be public. This is indeed the
> case, since it is said to be 'The name of the election event'."

And the concern it defends against, in the same note:

> "one can imagine other adversary constructions of the prime *p* where
> some multiplicative relation between the ℓᵢ's is known to the person
> who constructed the prime and could therefore easily (in polynomial
> time) break SGSP."

**What actually delivers that property.** System Specification §3.2
restricts the seed to `CT_YYYYMMDD_XYnm` — canton (2), election date
(8), TT/TP/PP plus a 2-digit ascending sequence. For a productive event
in a given canton on a legally-fixed date, the only free field is the
sequence number: **at most ~99 candidate primes.** That bound is what
makes prime-grinding hopeless, and it is a real, well-designed control.
Verification 5.01 checks the format and recomputes (p,q,g) from the
seed, so it is enforced, not just written down.

**The candidate: that control is documented as a naming convention.**
Computed, not eyeballed:

```
TERM TRACE: 'SGSP'
     Computational proof            : 43 mentions
     Gaudry SGSP note               : 20 mentions
  !! System Specification v1.6.1    :  0 mentions
  !! Verifier Specification v1.7.1  :  0 mentions
```

Zero in both documents that define and enforce the control. The only
rationale §3.2 gives for the format is modulo-overflow prevention, which
is about the *size* of the primes, not the *unpredictability* of p.

**And SGSP is the outlier, not the pattern.** Traced every named
assumption from the protocol's own Limitations section across the same
four documents:

| term | sysspec 1.6.1 | verifier 1.7.1 | comp. proof | Gaudry note |
|---|---:|---:|---:|---:|
| **SGSP** | **0** | **0** | 43 | 20 |
| quantum | 3 | 0 | 1 | 0 |
| malicious client | 2 | 0 | 0 | 0 |
| trustworthy setup | 1 | 0 | 3 | 0 |
| vote secrecy / privacy | 10 | 2 | 29 | 0 |
| trust assumption | 7 | 0 | 49 | 0 |

The System Specification discusses **every** other named assumption —
quantum adversaries, malicious clients, the trustworthy setup component,
trust assumptions generally. It is not a document that omits proof-level
concerns. SGSP is the single one it never names, and it is also the one
Swiss Post itself flags as least studied, *and* the one whose protection
is a restriction written into that very document.

That comparison is what makes this worth submitting rather than
shrugging at.

**Why it is worth submitting anyway, at Low.** It is not a
vulnerability and must not be presented as one. It is a load-bearing
security property presented as a formatting rule — precisely the shape
of thing a future revision relaxes (a longer sequence field, free-text
event names) without anyone noticing what it was holding up. A
one-sentence cross-reference from §3.2 to the SGSP assumption closes it
permanently.

**✅ THE UNKNOWN IS RESOLVED, 2026-09-04 — the candidate SURVIVES.**
`crypto-primitives` cloned at tag `crypto-primitives` HEAD and read.
Evidence:

- **SGSP appears ZERO times** in crypto-primitives source and docs. (One
  grep hit exists — a base64 blob in a mixnet test fixture that happens
  to contain the substring "sgsp" — a false positive, not a mention.)
- The control **is implemented**:
  `EncryptionParameters.getEncryptionParameters(seed, smallPrimes)`
  derives `q` from `shake256(seed)`, so a public election-event-name
  seed fully determines `(p, q, g)`. Real, well-built.
- Its javadoc documents **only** *"executions with the same seed yield
  the same encryption parameters"* and *"seed = the name of the election
  event"* — the reproducibility property. **No mention of SGSP, no
  mention that the public, constrained seed is what prevents an
  adversary constructing a special-form prime.**

So the finding is confirmed across **all three** reachable sources
(System Spec 0, Verifier Spec 0, crypto-primitives 0). The security
rationale for the seed constraint lives only in Gaudry's commissioned
note, which is not part of the spec or the code. **This is a real,
submittable Low-severity documentation finding.** It is not a
vulnerability and must not be presented as one: a one-line
cross-reference from the parameter-generation code/spec to the SGSP
assumption closes it.

Reproduce: `operator_cli spec --trace SGSP <sysspec.pdf> <sgsp.pdf>`, or
`grep -rc SGSP` across the three repos.

#### ✅ THE 2026 HIGH (€19,000 cache bug) — VERIFIED CLOSED in 1.6.1

Traced the exact 2026 High through source at the pinned post-fix tag
`e-voting-1.6.1.0`. Every category stated with its evidence:

- **VERIFIED — poisoning half fixed.** `evoting-libraries …/caching/
  GqGroupCache.java`: the cache key is now the composite record
  `GqGroupCacheKey(p, q, g)`, derived from all three of p, q, g. A
  different `g` yields a different key, so the legitimate entry cannot be
  shadowed. The 2026 "keyed only by p" defect is gone.
- **VERIFIED — deserialization-cache growth fixed.**
  `GqGroupCache.getGqGroupFromContext()`: on a cache **miss** it returns
  a transient group and does **not** `put`. The map can no longer grow
  from request input.
- **VERIFIED — native fixed-base cache not reachable from the voting
  path.** The only allocators of fixed-base tables are the warm-up paths.
  `publishGqGroupCreationEvent` has **zero callers** in crypto-primitives;
  `modExponentiate`/`multiModExp` allocate nothing per call. The one
  request-path allocator, `RequestCcKeysController` (config phase,
  `saveElectionEventContext → warmUpCaches`), sits **behind a
  fail-closed canton-signature gate**: `verifyPayloadSignature` throws on
  null signature, on `SignatureException`, and on `isSignatureValid ==
  false` — no log-and-continue path exists.

**Conclusion: the 2026 High is fully patched in 1.6.1. Stop hunting this
class here — no sunk-cost.** This is a verified negative, not a paying
finding, and it is worth exactly what it is: it tells us where NOT to
spend the next hundred hours.

**Scope limit, stated honestly:** this verifies the *specific* 2026
vector against *static source* at one tag. It is not a claim that
voting-server is secure, and it is not dynamic proof — a static read can
miss a path where the signature gate is reachable by another route. Full
assurance needs the system running (the deployable-server clone), which
remains the real next lever for fresh classes.

#### ✅ THE DEPLOYABLE-SERVER BUILD IS POSSIBLE, NOT BLOCKED — 2026-09-05

Last cycle I called the build "toolchain-blocked" (no JDK/gradle on the
host). That was an assumption. Resolved with evidence:

- `docker manifest inspect registry.gitlab.com/…/evoting-build:1.6.1.0`
  succeeds **anonymously** — the build image is public, no auth needed.
- **887 MB** compressed, 9 layers. Host has **724 GB** free disk and
  **22 GB** free RAM. Ample.
- The image is a self-contained build environment (JDK, gradle, node) —
  it *is* the missing toolchain.

So the build is **BUILDABLE**, not blocked. What remains true: it is a
**multi-cycle** undertaking (build a Java+Node multi-module tree →
tarball → then orchestrate the runnable stack: control components, HSM
sim, PostgreSQL, message broker), with a **low expected payoff per
cycle** — the target just survived 38 hunters and its confirmed class is
patched (verified last cycle). **Whether to make that investment is a
strategic call reserved for Kyle**, not something to sink an autonomous
cycle into unilaterally. Recorded as a decision, not executed.

Command to start it, when Kyle decides:
`docker pull registry.gitlab.com/swisspost-evoting/e-voting/evoting-e2e-dev/e-voting/evoting-build:1.6.1.0`
then run per `e-voting/BUILDING.md`.

#### Priority-4 re-sweep, 2026-09-05: market quiet

Live 7-source hunt, date-bounded: fetched 470, assessed 120,
**QUALIFIED=0**, INSUFFICIENT_DATA=99, DISQUALIFIED=21. Same stable
distribution as prior cycles — no new actionable cyber notice. Verified
negative, recorded so the next cycle doesn't re-run the identical query
expecting different output.

#### ❌ Swiss Post's source cannot be fetched by an automated agent

Attempted 2026-09-04. **This is a block, recorded as a finding, not
worked around.** The source and specification live on `gitlab.com`,
whose `robots.txt` disallows every mechanical route to file *contents*:

```
Disallow: /*/raw          Disallow: /api/v*
Disallow: /*/archive/     Disallow: /*/*.git$
Disallow: /*/repository/archive*
```

`/-/blob/` and `/-/tree/` are permitted, but those pages render
client-side — fetching one returns a page whose body is the word
"Loading". Swiss Post's own site (`swisspost-digital.ch/evoting-community`)
links to GitLab rather than mirroring the documents.

**This blocks the automated agent, not Kyle.** `robots.txt` governs
crawlers. A person opening the repository in a browser, or running
`git clone https://gitlab.com/swisspost-evoting/e-voting/e-voting.git`,
is an ordinary user doing an ordinary thing. The material is fully
available to you with one command — it just cannot be pulled unattended.

**A related judgment call, flagged rather than acted on.** Dovecot's
source is on GitHub, which also disallows `/*/raw/`, `/*/tree/` and
`/*/archive/` — but `raw.githubusercontent.com` serves no `robots.txt`
at all (HTTP 404), which under RFC 9309 means unrestricted. Those are
two different origins with two different published rules, so using the
permissive one is arguably correct rather than evasive. **Not done
either way without you saying so** — it is exactly the kind of call
that should not be made quietly at 3am.

#### The income report was hiding whether a programme pays

Three defects, all found by running it against the live board:

1. **`NOT_OBSERVED` was doing double duty**, and it is this repository's
   own UNKNOWN-is-not-ZERO rule running *backwards*. YesWeHack Dojo
   declares `bounty: false` — an observed fact that it pays nothing —
   and it was reported as "we did not see a payout", identical to an HN
   hiring comment that simply publishes no rate. Opposite states,
   collapsed. Now `DECLARED_NO_BOUNTY`, rendered as
   **PAYS NOTHING (platform declares no bounty)**.
2. **The payout column rendered only in the NEW block.** After the first
   run nothing is ever new — so the list an operator actually scans
   carried no payout at all, and a programme paying nothing sat
   indistinguishable from one paying €230,000. Both blocks now share one
   rendering function so they cannot drift apart again.
3. **`report_submission_cost` was not captured.** Every one of the 60
   programmes declares it: 51 carry `2`, and it rises with programme
   value — **TeamViewer 5, Swiss Post e-voting 7**. **The API states no
   unit anywhere.** It is *not* known to be money, and the field is
   named `report_submission_cost_unit_unknown` so no one can read a
   currency into it by accident. Whatever the unit, submitting against
   the high-value programmes is declared to cost more.

---

### 3. Ireland — NINE cyber qualification systems with no closing date at all ⭐

**Found 2026-09-03 by walking the entire Irish register — 293 pages,
2,921 open notices — instead of the first 200 rows every previous sweep
could reach.** Every one of these was sitting past page 20. None of them
is new; they have been open for months or years, and this campaign could
not see them.

These are **Dynamic Purchasing Systems** and **Qualification Systems**,
not tenders. The distinction is the entire point:

- A tender closes. These have **no closing date** — the deadline field
  is genuinely empty, not unread.
- A tender is a competition you win or lose. A DPS is a **qualification
  you either meet or do not**, and once admitted you are invited to the
  mini-competitions run under it for its whole life.
- Under EU Directive 2014/24/EU Article 34 a DPS must stay open to any
  operator meeting its selection criteria for its entire period of
  validity. **That is the law's definition of the instrument. Whether
  each specific system below is still admitting is UNKNOWN until its own
  documents are read** — `Established` is the platform's status word for
  the system, not a statement about admission.

| Resource ID | System | Contracting authority | Stated value |
|---|---|---|---|
| `7959367` | DPS for the provision of **Managed ICT Security Services** | Asiera CLG | **€175,000,000** |
| `6565390` | 25P041 DPS for **Cyber Security Services** | RTÉ | **€7,500,000** |
| `2485277` | DPS Qualification: **Managed Threat Detection and Response** | HSE | **€60,000,000** |
| `3635831` | HSE 23097 DPS: **CISO Threat and Vulnerability Management** | HSE | **€60,000,000** |
| `3234213` | DPS for **Unified Cyber Incident Response Service** | HSE | **€16,000,000** |
| `1943031` | DPS for the Unified Cyber Incident Response Service | HSE | UNKNOWN |
| `3243649` | CIE 7289 **Qualification System for Penetration Testing** | Iarnród Éireann | UNKNOWN |
| `1749698` | CIE 7289 Qualification System for Penetration Testing | Iarnród Éireann | 0.0 (as published) |
| `3009835` | 23/049 **Cyber Security Services** | Gas Networks Ireland | UNKNOWN |

Each is at
`https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=<ID>`

**Why this outranks the five dated Irish tenders already on this board.**
All five of those came back CANNOT APPLY, and every one of them failed on
the same thing: corporate reference contracts you do not have. A dated
tender asks "prove you have already done this at this scale, twice, in
the last three years." Admission to a DPS asks whether you meet the
selection criteria — which may ask the same thing, and may not. **The
criteria have not been read. This is a promising unread lead, not a
qualification.** The two Irish Rail penetration-testing entries are the
most interesting: penetration testing is the narrowest, most
individual-scale service on the list.

#### Two of the nine have now been read in full. They do not agree.

**❌ RTÉ 25P041 — CANNOT APPLY.** The DPS document was downloaded through
eTenders' own anonymous-download control and read. Admission is six
Pass/Fail gates (P1 Eligibility, P2 Financial, P3 Insurance, P4 Staff,
P5 Quality, P6 H&S). Two of them close it:

> **P2 Financial and Economic Standing** — "Tenderers must have achieved
> a minimum turnover level of **€350,000** in each of the three (3)
> previous financial years."
>
> **P3 Minimum Insurance Requirements** — "Tenderers must maintain the
> following minimum levels of insurance cover: Public Liability
> **€6.5M**, Cyber Insurance **€1.0m**, Professional Liability **€1.0m**"

Both are Pass/Fail **at admission**. No insurance means no admission.
Deadline for requests to participate is 30/10/2030, so it will still be
there if that ever changes.

**✅ IRISH RAIL CIE 7289 — THE BEST LEAD THIS CAMPAIGN HAS FOUND.**
Pre-Qualification Questionnaire (`PQQ/CIE/Version/2/18`), read in full.

> **5.1 MINIMUM QUALIFICATION CRITERIA** — "(1) Minimum Financial
> Qualification Criteria: (PASS/FAIL) **TURNOVER** (exclusive of VAT): A
> minimum annual turnover of **250k** per annum for the last three
> audited financial year ends."

That is the lowest financial bar found anywhere in Ireland, and it is
the **only** Pass/Fail criterion. Then, in the buyer's own words,
immediately after it:

> "**Reliance on resources to meet Turnover Requirement:** Where the
> Applicant seeks to rely on the resources of any third party to meet
> the above stated Minimum financial qualification criteria of Turnover
> ... it must provide evidence of the turnover for such other
> persons/entities for each of the financial years listed above and
> prove to CIE that the necessary resources will be available to it when
> required."

Followed by named routes for **Reliance on a Consortium Member**,
**Reliance on a Sub-Contractor**, and **Parent company**. This is the
mechanism documented further down this board — here applied to a
qualification system with **no closing date**, for **penetration testing
specifically**, at the lowest turnover threshold on record.

**And the sentence that separates this from every other Irish notice:**

> "Applicants should note that those who have been **selected to
> Call-Off stage**, will be required to comply with the insurance
> requirements of the IE Standard Contract and will be required to be in
> possession of and produce a **Tax Clearance Certificate from the
> Revenue Commissioners of Ireland** at time of contract award."

That is the **only** mention of insurance in the entire PQQ. Insurance
here is a **call-off obligation, not an admission gate** — the exact
opposite of RTÉ and of all five dated Irish tenders. It means Kyle can
be admitted to the qualification system now, and only needs cover if and
when actual work is on the table.

Technical/Professional Ability is **scored, not Pass/Fail** — 40%
minimum per criterion, weighted across Resources and Capacity (20%),
Quality Management (10%) and others. Client references are sought as
feedback, not required as a gate.

**Still UNKNOWN, and both matter:**
1. **The PQQ deadline.** The register shows this system as `Established`
   with an empty deadline field, and the PQQ says submissions are due by
   a date "stated on the front cover" — which sits in a document field
   that did not extract. **Check the front cover before assuming it is
   still open.**
2. **The Tax Clearance Certificate.** Irish Revenue issues these to
   non-resident suppliers, but whether an Australian sole trader can
   obtain one, and how long it takes, has not been verified here.

**ACTION, in this order:**
1. Open `https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=3243649`
   and check the PQQ front cover for a submission deadline.
2. If open: the turnover gate is €250k × 3 years and the document itself
   names four sanctioned ways to meet it with someone else's resources.
   That is a conversation with an established firm, not a wall.
3. Do **not** start with RTÉ. It is a definite no on quoted clauses.

**✅ THE READINESS CHECKLIST IS NOW COMPUTED — 2026-09-05.**
`python3 -m foundation.operator_cli dossier` now covers both live Irish
leads (they were absent — it only knew the four AU/UK schemes). For each
it prints the exact, quoted, still-missing facts that need *your* input:

- **Irish Rail 7289:** audited €250k/yr turnover **or** a third-party
  reliance declaration; Irish Tax Clearance obtainability (deferred to
  award, does not block applying); a signed PQQ declaration; scored
  pen-test experience/references. Insurance is deferred — not needed to
  apply.
- **GNI 23/049:** €175k avg turnover (pro-rata for a young business); a
  broker letter that cover *can be arranged* (not held); a bank-standing
  declaration; scored experience — with the carve-out that personal
  employment experience cannot be counted.

Every line quotes the real criterion. This is preparation material only,
stamped DRAFT — a human transcribes, verifies, and signs. It converts
the two leads from "promising" to "here is precisely what to prepare."

**⚠️ GAS NETWORKS IRELAND 23/049 — read third, and it changes the shape
again.** Lower bar than Irish Rail on money, harder on experience.

> **D1 Turnover (Pass/Fail)** — "an average annual turnover, in the last
> 2 years **or pro-rata for a company established within the last 2
> years** of at least: **€175,000**"

Lowest financial threshold found in Ireland, and the pro-rata clause is
written for a young business. Insurance is stranger and better than it
looks:

> **F1 Insurance requirements** — "The Applicant is to provide a letter
> from their insurers/brokers stating the following: We, the
> insurers/brokers to [Applicant] hereby confirm that the following type
> and level of cover **can be arranged** on the Applicant's behalf"

Cover that **can be arranged**, not cover already held — a broker's
letter, not a policy. Levels are large (Public Liability €6.5m, Products
Liability €6.5m, Employers Liability €13m, plus Professional Indemnity).

The gate here is experience, scored not Pass/Fail — Financials 150 (75
to pass), Resources 375 (175), **Experience 375 (175)**, Data Protection
50 (30), Information Security 50 (30). Reliance on another entity's
resources is permitted, with one carve-out that lands directly on a solo
operator:

> "previous experience gained by: **an individual while working for a
> third-party entity** ... cannot [be relied upon]"

Kyle's own past work for employers cannot be counted as his business's
experience. That is the clause to read in full before spending effort
here.

Round 1 queries closed 13 February 2024. A qualification system admits
continuously, so later rounds should exist — **UNKNOWN, and worth one
message through the eTenders facility before doing any work.**

#### ALL NINE ARE NOW RESOLVED — 2026-09-04

Every remaining document was downloaded and read. The result is one live
lead, one maybe, five hard noes and two unread-for-a-stated-reason.

| System | Verdict | The clause that decides it |
|---|---|---|
| **Irish Rail CIE 7289** (×2, same PQQ) | ✅ **PURSUE** | €250k turnover, four written routes to meet it with a third party, insurance deferred to call-off |
| **Gas Networks Ireland 23/049** | ⚠️ **MAYBE** | €175k pro-rata, insurance only "can be arranged" — but personal employment experience explicitly excluded |
| **Asiera / HEAnet €175M** | ❌ | "must provide their SOC and Incident Response Services on a **24 hour a day, 7 days a week, 365 days a year**" basis |
| **RTÉ 25P041 €7.5M** | ❌ | Public Liability €6.5M / Cyber €1.0M / Professional €1.0M, **held**, Pass/Fail at admission |
| **HSE 21236 Managed Threat Detection €60M** | ❌ | staff-in-Ireland + Dublin on-site (below) |
| **HSE 22167 Unified Cyber IR €16M** | ❌ | same clause, same document family |
| **HSE 22167 (second entry)** | ❌ (inferred) | same HSE ref 22167 — **inferred, not separately read** |
| **HSE 23097 CISO Threat & Vuln €60M** | **UNREAD** | its document exceeds the fetcher's 5 MB cap — see below |

**The HSE clause, quoted, and it is not about money at all:**

> **IV.5 Service Provision** — the service "can be provided
> **24/7/365** for the lifetime of the contract", "is **delivered by
> staff based within Republic of Ireland**", "Cyber IR **onsite within
> 24hrs**", "Service provider must be able to provide **Dublin based
> non-contract resources** to support on-site".
>
> **IV.4 Relevant Experience** — "supplied on at least **three (3)
> occasions**' products or services similar in scope ... in the last
> three (3) years", with contract values and references. 200 of 400
> marks to pass.

HSE's insurance clause is actually soft — "has in place (**or has the
ability to obtain**)" — and its financial test is about outstanding
claims and audit opinion, not a turnover number. It doesn't matter. A
Cairns sole trader cannot base staff in the Republic of Ireland or put
someone in Dublin within 24 hours. That is a geography wall, and it is
the first one this campaign has hit that money cannot move.

**Asiera is the same story from the other direction.** Its admission
document was the softest found anywhere — turnover "exceeded €500,000 in
**any** of the last three financial years, **or pro-rata if more
recently established**", insurance satisfiable by "a statement
confirming that should the company be **awarded the contract**, it is
willing and able to raise its insurance cover to these levels", tax
clearance satisfiable by confirming you have *applied*. Then Part B, the
per-lot half, asks for a 24×7×365 SOC, **three named customer
references** with addresses and phone numbers, and evidence of a single
order worth **€80,000/year**. Soft front door, locked back door.

**One is genuinely unread, and the reason is a limit in our own code.**
HSE 23097's document set is served as `T4 for etenders.zip`, which
`mouth_common.fetch_feed()` refused:

```
exceeds MAX_FEED_BYTES (5242880) — refusing to buffer an unbounded
remote response; treated as UNAVAILABLE
```

That cap is correct and should not be raised to read one file. Recorded
as UNREAD rather than guessed at from its siblings — HSE's other two are
noes, but "probably the same" is not a reading.

**What nine readings establish: the instrument tells you nothing.**
Five different admission shapes appeared under the same three letters —
insurance held at admission (RTÉ), insurance deferred to call-off (Irish
Rail), insurance as a broker's arrangeability letter (GNI), insurance as
a promise to raise cover if awarded (Asiera), and insurance as a
self-declared ability to obtain (HSE). "It's a DPS" predicts nothing.
Each one had to be opened.

#### ✅ PRIORITY 3 (deep Ireland) IS EXHAUSTED FOR KYLE'S PROFILE — 2026-09-05

Scanned **all 656 rolling systems** in the walked register for IT/security
work from buyers not already analysed. Result: **4 hits, none reachable**
— Cork City Council consultancy panel, IPA design/development panel, OGP
compute/storage infrastructure supply, Uisce Éireann software-licensing.
All are infrastructure supply / generic consultancy / reselling, not
solo cyber-services. The reachable set — the 9 cyber DPS + the 3 Iarnród
Éireann ICT systems (7162, 7289, 7764) — was already fully read. The rest
of the CIE family is rail engineering (bridges, steel, surveys) a Cairns
cyber operator cannot bid on. Verified negative; this seam is mined.

#### One buyer runs a whole family of these, on the same template ⭐⭐

The nine cyber systems were found by a **security keyword**. Widening to
the whole register: **656 of the 2,921 open Irish notices — 22% — have
no closing date at all.** Every one is an `Established` DPS or
Qualification System. The security nine were a slice of a much larger
standing market this campaign never knew existed.

Inside it, **Iarnród Éireann / CIE runs at least four rolling ICT
qualification systems on the same PQQ template** whose penetration-
testing version already reads as the friendliest in Ireland:

| Ref | System | Minimum turnover (Pass/Fail) |
|---|---|---|
| `3151458` | **7162 ICT Consultancy Services** | **€200k**/yr per lot |
| `3245545` | **7764 ICT Professional Services** | Lot 6 **€200k**, Lots 1 & 4 €250k, Lot 3 €300k, Lots 2 & 5 €350k |
| `3243649` | 7289 Penetration Testing | €250k |
| `3245805` | 7292 Licensing & Software Maintenance | not read |

Verified in each document read: the **same** turnover clause wording,
the **same** "Reliance on resources to meet Turnover Requirement"
paragraph permitting a third party's turnover, and insurance appearing
**exactly once**, deferred:

> "Applicants should note that those who have been **selected to proceed
> to tender stage**, will be required to comply with the insurance
> requirements of the Contract and be required to be in possession of
> and produce a **Tax Clearance Certificate** from the Revenue
> Commissioners of Ireland at time of contract award."
> — 7162 and 7764, identically

**€200k per annum is the lowest financial bar found anywhere in this
campaign**, and it is met with someone else's turnover by a route the
buyer wrote down itself. Multi-lot applications aggregate the
requirement (7764: Lots 1+2 = €600k), so **apply for one lot, not
several** — the aggregation rule is how an applicant accidentally
triples their own bar.

One buyer. One document shape. Four ways in. If a conversation with CIE
works once, the template is already understood for the rest.

#### ✅ THE DEADLINES — RESOLVED 2026-09-04, AND THEY ARE YEARS AWAY

Two cycles of this board recorded the PQQ deadline as UNKNOWN because
"the front cover did not extract". **That was wrong.** The text was in
the document the whole time; I searched the wrong offset — the cover
page sits past the header block, not at character zero. Quoted from the
documents themselves:

| System | CLOSING DATE FOR RETURN OF COMPLETED QUESTIONNAIRE |
|---|---|
| **7289 Penetration Testing** | "**Before Jan 2029**" |
| **7162 ICT Consultancy** | "**Open for application till Feb 2029**" |
| **7764 ICT Professional Services** | "**6th April 2029**" |

All three are open for years, not weeks. There is no deadline pressure
on the best lead this campaign has found — which changes the sequencing:
this is a thing to do properly, not quickly.

**One UNKNOWN genuinely remains:** whether an Australian sole trader can
obtain the Irish Tax Clearance Certificate the documents require at
contract award. Note where that requirement sits — Irish Rail defers it
to *contract award*, not admission, so it does not block applying.

**And the real gate is not insurance.** It is the 24×7 staffed service
and the named-reference requirement — three of the nine demand a
round-the-clock operation, which no amount of insurance, turnover or
subcontracting rhetoric gets a solo operator past. Irish Rail is the
exception because **penetration testing is project work, not a
staffed service.** That is the actual selection rule, and it is worth
carrying to every future sweep: *look for the engagement-shaped
services, not the operations-shaped ones.*

---

### 4. Horse Racing Ireland — Network Security, €2,100,000 ⏰ CLOSES 8 SEPTEMBER

| | |
|---|---|
| **Title** | Single Framework for the Provision of IT Support Services - Network Security |
| **Contracting authority** | Horse Racing Ireland (HRI) |
| **Value** | **€2,100,000** |
| **Deadline** | **8 September 2026** — five days from this sweep |
| **Resource ID** | `8781382` |
| **Status** | Tender Submission |

Also found only by the full-register walk. Criteria **NOT READ** — this
is a title, a value and a date, nothing more. Given every other Irish
notice this campaign has opened demanded reference contracts and
insurance, the honest prior is that this one does too. It is listed
because five days is not enough time to find it twice.

---

### 2. ADB Consultant Management System — the modality built for people

Every barrier on this board — €13,000,000 employer's liability,
€2,600,000 turnover, three corporate references — exists because the
buyer was procuring from a **firm**. Development banks run a separate
track for procuring from a **person**, and it does not carry those
requirements because there is no company to carry them.

**What I verified myself, 2026-09-03:**

| | |
|---|---|
| `cms.adb.org` | **live, HTTP 200, publicly reachable** |
| robots.txt | permits it — only `/admin/`, `/user/`, `/search/` disallowed |
| Registration | open: *"Don't have an account yet? Register here."* |
| Menu | Consulting Opportunities · Shortlisted Firms · Awarded Contracts |
| **Australia's ADB membership** | **1966** — quoted from ADB's own members page |
| ADB founded | 1966, with 31 members. **So Australia is a founding member.** |
| Members today | 69 |

**What I could NOT verify, and it is the load-bearing part.**

A research pass reported ADB's individual-consultant eligibility as
*"a citizen of an ADB member country, not barred, not a close relative
of an ADB staff member"* — with no incorporation, insurance, turnover or
reference requirement. If accurate that is the single most important
finding of this campaign.

**I could not confirm it.** Every CMS path — the registration page, the
terms page, the opportunities listing — returns the same 14,518-byte
shell, because CMS is a JavaScript application that routes client-side.
The rule is real or it is not; static fetch cannot tell you which, and
neither can I.

It is recorded here as **UNVERIFIED** rather than promoted to the top of
the board, because a wrong eligibility claim is exactly the error that
produced a false QUALIFIED on ECHA earlier in this campaign — and that
one cost a €1,000,000 turnover clause hiding in plain sight.

**ACTION, and it is small:** open `cms.adb.org` in an ordinary browser
and click Register. The form itself states what it requires. Ten minutes
answers whether the biggest structural opening found in nine cycles is
real.

**✅ WHY IT STAYS UNVERIFIED — RESOLVED 2026-09-03 (D-016).** The
eligibility rules could not be confirmed because the authoritative source
is unreachable to an honest agent: **adb.org returns HTTP 403** (WAF —
even `/robots.txt` 403s), and `cms.adb.org` is a JS SPA. The whole
individual-consultant lane was checked the same way — **UNDP disallows all
crawling (`robots.txt: Disallow: /`)**, the EU expert portal is a
client-rendered shell, UNGM/World Bank expose no static eligibility page.
**The lane is human-browser-only**; no automated sweep is possible without
evading a WAF or a robots rule, which is refused. So ADB stays UNVERIFIED
with a specific reason now on record, and the resolving action is
unchanged — Kyle's ten minutes in a browser. See `docs/DECISIONS/D-016`.

**Related, same class, same unresolved status:** UNGM's registration
reportedly offers "Individual Consultant" and "Sole proprietor" account
types with no incorporation requirement. UNOPS's Individual Contractor
Agreement, the World Bank's individual-consultant track and the EU
expert roster are all JavaScript applications that static fetch cannot
read. All four are reachable and unblocked — none is confirmed.

---

#### ✅ NZ GETS PRE-QUALIFICATION SWEEP — RESOLVED 2026-09-03 (was 3/36)

Priority 1 asked whether the remaining GETS security notices each state
"Required Pre-qualifications: None". **They do — uniformly.** This cycle
walked the live GETS feed (323 open notices), filtered to the 23
genuinely IT/software/cyber notices (dropping physical security —
guards, CCTV, fire alarms, HVAC — that the keyword net catches), and
read each one's own detail-page `Required Pre-qualifications` field
through the already-wired `mouth_gets_nz.fetch_tender_detail` (gated,
6–13s between fetches, honest User-Agent, robots.txt permits all but
SemrushBot).

**Result: 22 of 22 read = `Required Pre-qualifications: None`.** Every
IT notice, including Identity Management Services, Enterprise
Observability, Technical Support Services (TSS) Panel Reset, Medical
System Project, Datacentre Co-location, Regional Internet, Network
Service Provider, Data Science & Analytics. Not one carried a
platform-level pre-qualification gate. (One notice, Data Science &
Analytics Platform, dropped off the feed between two fetch passes — a
live feed rotating, recorded as such, not as a block.)

**What "None" means, stated honestly — this is the trap.** GETS's
`Required Pre-qualifications: None` means only that no GETS-platform
prequalification questionnaire blocks viewing or downloading the RFP.
It is **not** a statement that the tender has no bidder requirements —
the real financial/insurance/experience criteria live inside each RFP's
own attached documents, which sit behind the free GETS supplier login
(the same wall documented below for the Marketplace SOI: "appropriate
insurance provisions", "demonstrate relevant experience", no figures on
the public notice). So the finding is precise: **nothing on the GETS
platform stops Kyle registering and reading any of these — the gate, if
any, is inside the documents, and those are UNKNOWN until a logged-in
human opens them.** Absence of a stated pre-qual is not absence of a
requirement.

This closes priority 1: the sweep is complete for the IT-relevant slice,
the field is uniform, and the real question has moved from "is there a
prequalification wall" (answer: no, at platform level) to "what do the
login-gated RFP documents require" (answer: a human step, below).

---

### 2. NZ Government Marketplace — all-of-government IT, open to 2029, international

Found 2026-09-03 by the new notice classifier, which is the only reason
it surfaced: it had been sitting in every NZ sweep since the start,
scoring `INSUFFICIENT_DATA` alongside 324 other notices.

| | |
|---|---|
| **Buyer** | Department of Internal Affairs |
| **Type** | Invitation to Participate (ITP) |
| **Coverage** | **All of Government** |
| **Open** | 25 March 2026 → **closes 25 May 2029** |
| **Categories** | 43000000 Information Technology · **81110000 Computer services** · 81160000 IT service delivery |
| **Regions** | **International** |
| **Required Pre-qualifications** | **None** |
| **URL** | gets.govt.nz//DIA/ExternalTenderDetails.htm?id=33732411 |

Read that row set again. An **all-of-government** IT marketplace, in
**computer services**, explicitly **international**, with
**pre-qualifications stated as None**, open for another **two years and
eight months**.

It is the New Zealand analogue of the NSW ICT Services Scheme — except
NZ states the international eligibility outright, and NZ's procurement
rules already confirm they *"do not discriminate against suppliers
(domestic or international)"* under the Australia New Zealand Government
Procurement Agreement.

**No deadline pressure, no credential gate published, and a buyer that
covers every NZ government agency.**

**THE APPLICATION CRITERIA, read 2026-09-03 from marketplace.govt.nz.**
The channel open for application is literally **Managed Security
Services** (alongside Infrastructure and Telecommunications). Quoted:

> *"accept the Collaborative Marketplace Agreement terms"*
> *"be an active and legitimate business"*
> *"be financially viable to provide the services applied for"*
> *"have in place appropriate insurance provisions"*
> *"should not be involved in disputes or legal proceedings"*
> *"demonstrate relevant experience in the services they applied for"*
> *"demonstrate relevant capability and capacity to provide services"*
> *"provide required security information"*

**No turnover threshold. No insurance amount. No certification named. No
reference count.** Compare to Ireland, where four of five buyers wanted
€13,000,000 employer's liability and three reference contracts, and
turnover ran €400,000 to €2,600,000.

And the buyer's own framing of the whole scheme:

> *"The Marketplace simplifies how the NZ Government buys ICT and lowers
> the barriers for suppliers to provide us with services — in short, the
> Marketplace makes it easier for suppliers — large and small — to do
> business with government."*

**What is still genuinely UNKNOWN, and matters:**

- *"appropriate insurance provisions"* names no figure. Undefined is not
  absent — it could still mean $5M public liability at contract stage.
- *"demonstrate relevant experience"* names no threshold. This is the
  clause most likely to bite, and it is the same shape as the referee
  question outstanding at NSW.
- The detailed security documents (Marketplace Information Security
  Tiering Standard, GCDO Continuous Security Certification Controls
  Validation Plan, and four scoping templates) are **only available
  after registration begins.** They are listed on the GETS notice as
  attachments, so they exist and they are substantial.
- **Whether a sole trader may apply is not stated either way.** The
  criteria say "business" and "company" without defining or excluding.
  UNKNOWN, and worth one email.

**THE APPLICATION QUESTIONS ARE BEHIND A FREE ACCOUNT — a human step.**
The GETS notice lists its attachments, and one is literally *"Standing
Notice of Procurement: Appendix 2: The I/TMS Application questions"* —
the exact document that would answer what the application asks. On the
anonymous page every attachment link routes through
`TendererLogin.auth`. That is a supplier account, not a paywall and not
a block: free to create, and this cycle will not create one because
account creation is yours, not mine.

**Ten minutes with a GETS account gets you the actual application
questions, the Information Security Tiering Standard, and the four GCDO
certification scoping templates.** Everything currently marked UNKNOWN
above is inside those files.

Contact published on the notice: `marketplace@dia.govt.nz`, and their
own site currently warns *"Due to high demand, it may take us longer
than usual to process applications"* — which is a live scheme, not a
dormant one.

Also live, same class, same buyer type:

- **All-of-Government Construction Consultancy** — Standing Open
  Invitation, MBIE, closes 30 Sep, pre-qualifications None. Wrong
  category for you, listed only because it confirms the pattern: NZ runs
  several of these standing invitations and they recur.

---

### 2. NSW ICT Services Scheme (SCM0020) — $150,000 contract ceiling

| | |
|---|---|
| **Value** | Contracts up to **$150,000 ex GST** at the Registered tier |
| **Gate** | An ABN. That is the hard requirement |
| **Turnover** | **Not an acceptance criterion** — quoted from their own FAQ: *"It is requested for informational purposes but does not form part of the acceptance criteria"* |
| **Insurance** | $1M PI / $5M PL required **before entering an agreement, NOT to join**. PBD 2023-03 exempts SMEs from proving it until contract award |
| **Deadline** | None. Always open |
| **Fee** | None |
| **Assessment** | 2–3 business days typical, up to 14–15 maximum (the two source documents disagree; both figures quoted, neither averaged) |
| **Category** | **K03 "Security testing"** — the exact label covering penetration testing, web security testing, secure code review |

**THE ONE BLOCKER:** Scheme Rules §8.1 requires **two referee reports**
per nominated category.

**But that blocker may not be real.** §8.1's full text on referees is
*"two (2) referee reports for each nominated high-level category"* — and
that is the **entire** mention of referees in the Rules and the FAQ,
both fetched and full-text searched. **"Referee" is never defined.**
Nothing restricts it to paying customers, government agencies, or
corporate clients. That restriction was our assumption, not their rule.

No new-entrant or start-up waiver exists (full-text searched, zero hits).

**ACTION:** email `ICTServices@customerservice.nsw.gov.au` and ask
whether a documented pro-bono engagement qualifies as a referee. One
email resolves the only thing standing between you and a $150k ceiling.

**Still outstanding for this scheme (5 facts, all yours):** ABN, declared
service skills, two referee reports, Supplier Declaration signature,
financial solvency confirmation.

---

### 3. ICN Gateway — no reference gate at all

| | |
|---|---|
| **Value** | Subcontracting exposure, not prime contracts |
| **Gate** | **Zero reference requirement.** ABN at signup (auto-populates from ABR) |
| **Deadline** | None |
| **Cost** | Free tier exists — **but** the "Limited" free tier does **not appear in buyer search results**. Discoverability needs a paid tier, reported ~$600–$1,480/yr |
| **URL** | gateway.icn.org.au |

**Confidence note:** the pricing figure was not fetched from ICN's own
pricing page and is lower-confidence. Confirm at signup.

**ACTION:** this is the route you can finish today without waiting on
the NSW referee answer. 2 facts outstanding: ABN, declared skills.

---

### 4. Queensland — no panel gate whatsoever

QITC has **no panel or accreditation gate**. Contracting is direct,
per-engagement, through QTenders.

**The catch, and it is a real one:** registering on the Supplier Portal
alone does not generate leads. Buyers reportedly check the Arrangements
Directory (`qgad.epw.qld.gov.au`), which is separate from QTenders and
needs active weekly monitoring.

**2 facts outstanding:** declared supply categories, business info and
service regions.

---

### 5. UK Crown Commercial Service — Cyber Security Services 3 DPS

| | |
|---|---|
| **Value** | £800,000,000 total DPS spend |
| **Open until** | **13 February 2029** — a DPS admits new suppliers throughout its life |
| **To join** | Selection Questionnaire + DPS Questionnaire |
| **Where** | supplierregistration.cabinetoffice.gov.uk/dps |
| **Turnaround** | 10 days |
| **Certification to join** | **None** |

Certification gates the **filters**, not entry — and one filter category
is explicitly **"Non-certified NCSC Services"**. That category exists for
suppliers in exactly your position.

A web claim that "Cyber Essentials is now baseline" was checked, could
not be sourced, and was discarded rather than repeated.

**3 facts outstanding:** DPS Schedule 1 filter selection (a human must
read the real document — we would not guess), SQ financial details,
declared service skills.

---

## TIER 2 — live, dated, act within weeks

### 6. City of Bradford MDC — penetration testing framework ⏰ 11 DAYS

| | |
|---|---|
| **Value** | **£300,327** |
| **Deadline** | **2026-09-14 16:00 UTC** |
| **Procedure** | Open Framework under the Procurement Act 2023 |
| **Award** | Council intends to appoint the **top 3 providers** |
| **Scoring** | Quality 40 / Social Value 10 / Price 50 |
| **Work** | 10-day consultancy packages, NCSC and OWASP standards |
| **Notice** | 2026/S 000-078110 |

**The notice states only that it seeks "a suitably experienced and
qualified Provider"** — no turnover, insurance, certification, staffing
or reference threshold appears anywhere in its text.

**DO NOT read that as clear.** PSN IT Health Check work is conventionally
performed by **CHECK-scheme accredited** testers, and that requirement
would sit in the tender documents rather than the notice. This is
**unresolved**, not cleared.

**✅ MUCH STRONGER EVIDENCE — 2026-09-05, from the authoritative OCDS
release** (`ocds-h6vhtk-06e59c`, Find a Tender's public keyless API, the
structured selection-criteria source, not the free-text summary). Scanned
the entire release:

```
CREST            0        certification    0        insurance   0
CHECK-scheme     0 *      Cyber Essentials 0        turnover    0
accreditation    0        ISO 27001        0        references  0
```
`* the two "CHECK" string matches are both inside "IT Health Checks" in
the title, not CHECK-scheme accreditation.`

**The authoritative notice data states ZERO qualification barriers.** The
only stated requirement is "a suitably experienced and qualified
Provider", the procedure is **Open** (no pre-selection), status **active**,
deadline confirmed **2026-09-14T16:00Z**, value £300,327 gross / £250,273
net. No public tender document is linked beyond the notice itself.

This is now a repeatable one-command check for any UK notice:
`python3 -m foundation.operator_cli fat-notice <ocid> --live` fetches the
notice's real criteria from the public OCDS release API and runs them
through the entry-gate barrier analysis. The UK free-text feed carries no
criteria (every UK notice was stuck at INSUFFICIENT_DATA); this wires the
authoritative structured path the mouth's own docstring had flagged as
unused.

**The honest limit, per our own rule (absence ≠ no requirement):** this
does not *prove* no CHECK requirement exists — the ITT / specification
annex lives behind `uk.eu-supply.com` and has not been read. But the
strongest structured evidence available now says every conventional
barrier is absent, which moves this from "probably needs CHECK" to "the
one place a barrier could still hide is the portal-gated ITT."

**ACTION — needs your browser, ten minutes, and it is time-critical (11
days):** open `uk.eu-supply.com` (session-cookie-gated, NOT WAF-blocked —
a human browser gets in where the fetcher cannot), download the ITT, and
confirm whether CHECK/CREST is required. Given the OCDS release shows no
barriers, an Open procedure, and top-3 appointment on your exact skill
(pen testing, NCSC/OWASP, 10-day blocks), **this is the highest-value
live item on the board and the only one with a near deadline.**

---

### 7. Ireland — two RESOLVED (both no), three still open

**2026-09-02 overnight: the documents are now readable.** eTenders'
document pages offer **"Proceed without association"** — anonymous
download is an option the site itself provides, not a control worked
around. The static path is
`/epps/cft/downloadContractDocument.do?documentId=<id>&resourceId=<id>`,
recovered by reading (never executing) the page's own JavaScript.

That closes the two biggest Irish notices with quoted evidence.

#### ❌ Health & Safety Authority — €900,000, closes 12 Oct — CANNOT APPLY

> *"Tenderers will either pass OR fail each of the Selection Criteria in
> this part 3.2. A Tenderer who fails a selection criterion will be
> excluded from participation."*

| Requirement | Threshold | You |
|---|---|---|
| Annual turnover, auditor-signed | **€1,800,000** | ✗ |
| Employer's Liability | €13,000,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Product Liability | €6,500,000 | ✗ |
| Professional Indemnity | €1,000,000 | ✗ |
| Cyber Security insurance | €2,500,000 | ✗ |
| Reference contracts | **3 of similar value, last 3 years** | ✗ |
| Bank letter confirming good standing | required | ✗ |

#### ❌ Fáilte Ireland — €800,000, closes 24 Sep — CANNOT APPLY

Section A is explicitly **"PASS/FAIL CRITERIA"** with a **"MINIMUM RULE
/ ELIMINATOR"**. Reference `IT/2026/08`, 3-year contract.

| Requirement | Threshold | You |
|---|---|---|
| Turnover, any of previous 3 financial years | **€400,000** | ✗ |
| Employer's Liability | €13,000,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Professional Indemnity | €2,000,000 | ✗ |
| Cyber Liability | €5,000,000 | ✗ |
| Reference contracts | **3 in last 3 years, similar scope, scale and complexity** | ✗ |

**ONE GENUINELY USEFUL CLAUSE, quoted verbatim:**

> *"NOTE #1: in the case of the Candidate being a grouping, the condition
> at (i) above may be satisfied by the group members as a whole."*

**Turnover can be met by a consortium as a whole.** That is written into
the rules, not inferred. It does not make you eligible alone — the
insurance and reference bars still apply to the grouping — but it is the
first explicit, quoted confirmation in this entire campaign that
**joining a group is a sanctioned route into contracts you cannot reach
solo.** It reframes the subcontracting lane from a workaround into a
procurement mechanism the buyer names itself.

#### ❌ An Post — SOC/SIEM, closes 29 Sep — CANNOT APPLY

Tender ref `0055`. Sections 2.1 Turnover, 2.2 Insurance, 2.3 Tax
Clearance and 2.4 Going Concern are each marked **(PASS/FAIL)**, plus
References 1, 2 and 3.

> *"TURNOVER (exclusive of VAT): A minimum annual turnover of one million
> euro (€1,000,000.00) per annum for any two of the last three financial
> year ends."*

Insurance limits: €13,000,000 / €6,500,000 / €2,600,000 / €3,000,000.

**But this one hands you the consortium route on a form field:**

> *"In the case of a consortium, the turnover threshold must be met by the
> combined annual turnover of all members of the consortium for any two
> of the last 3 audited financial year end."*

> *"Tick to confirm if Applicant is relying on combined turnover of
> consortium members or those of any other persons/entities, in order to
> meet the minimum financial qualification..."*

There is a **checkbox on the PQQ** for exactly this. Third independent
confirmation, and the most explicit.

#### ❌ Department of Justice — national PKI, closes 2 Oct — CANNOT APPLY, but closest yet

Contract up to €2,000,000; initial phase €450,000–€700,000.

| Requirement | Threshold | You |
|---|---|---|
| Turnover, each of last 3 years | **€800,000** | ✗ |
| Employer's Liability | €12,700,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Professional Indemnity | €1,000,000 | ✗ |
| Reference | PKI delivery **> €50,000** | ✗ |

**Two things make this the most solo-friendly document found anywhere:**

> *"Applicants must demonstrate access to at least the minimum numbers of
> skilled personnel stated. **Please note that the skills outlined may
> reside in the same person.**"*

A buyer explicitly accommodating one person holding several skills — the
opposite of degewo's "minimum 3 penetration testers". And the reference
bar is **€50,000**, against €100,000-and-similar-value elsewhere.

It still fails on turnover and insurance. But it proves the personnel
requirement is not universally a headcount test, and it is worth
watching this buyer for smaller future work.

#### ❌ Houses of the Oireachtas — closes 28 Sep — CANNOT APPLY, hardest of the five

Tender ref `2026/1021`, 88-page RFT, now parsed.

> *"Tenderers are required to demonstrate that they have a minimum
> average annual turnover of €2,600,000 (excl. VAT) in each of the last
> three financial years. Failure to demonstrate the minimum required
> turnover will result in the tenderer being eliminated from the
> competition."*

| Requirement | Threshold |
|---|---|
| Minimum average annual turnover, each of last 3 years | **€2,600,000** |
| Employer's Liability | €13,000,000 |
| Public Liability | €6,500,000 |
| **Professional Indemnity** | **€10,000,000 in aggregate** |
| Cyber Liability (incl. loss of data) | €5,000,000 |
| Evidence | Banker's statement within 6 months + 3 years audited accounts |

The highest turnover bar and the highest professional indemnity of any
notice assessed in this campaign — €10m PI against €1–2m elsewhere.

Award is 55% weighted on functional and technical merit (SIEM platform
management, SOC threat detection and response, incident response
retainer), which is genuine capability scoring — but you never reach it,
because §3.2 eliminates first.

---

### What five Irish documents establish

Five notices, five independent sources, one consistent shape:

| Buyer | Turnover | Employer's Liability | Prof. Indemnity | References |
|---|---|---|---|---|
| Oireachtas | €2,600,000 | €13,000,000 | €10,000,000 | prev. contracts |
| HSA | €1,800,000 | €13,000,000 | €1,000,000 | 3 |
| An Post | €1,000,000 | €13,000,000 | — | 3 |
| Dept of Justice | €800,000 | €12,700,000 | €1,000,000 | 1 × >€50k |
| Fáilte Ireland | €400,000 | €13,000,000 | €2,000,000 | 3 |

**€13,000,000 employer's liability appears in four of five, unchanged**
(the fifth is €12.7M). That is not five buyers each deciding
independently — it is a standard Irish public-sector template. The
barrier is therefore not negotiable per-contract, and it is
**predictable**: any Irish public security tender will want roughly
this. There is no point assessing them one at a time hoping for a
lenient buyer.

**Turnover is the figure that varies — €400,000 to €2,600,000, a 6.5×
spread — and turnover is precisely the one they let a consortium satisfy
jointly.**

All five documents were checked for the reliance clause. **All five
carry it.** The Oireachtas RFT, verbatim:

> *"Tenderers should note that where a Tenderer is relying on the capacity
> of other entities (for example, Subcontractors) for the purposes of
> fulfilling any of the Selection Criteria in part 3.2 below it must
> ensure that each such entity: (i) completes and submits a separate
> eESPD in respect of..."*

Five for five. This is not a quirk of one buyer — it is how Irish public
procurement is written.

**Deeper sweep, 2026-09-02:** 400 of 2,916 open Irish notices walked
(double the previous 200, 40 pages). Security-relevant hits: **7, of
which 5 are the notices already resolved above** and 2 are false
positives (an Irish Rail mediation system, an internal communications
platform).

**No new Irish security work exists in the visible half of the
platform.** The five resolved notices are the Irish market right now,
and all five are closed to a solo bidder. That is a complete answer for
Ireland, not a partial one.

eTenders carries 2,916 open notices against TED's 746 Irish ones, so
roughly 2,170 remain below TED's threshold and structurally invisible to
it. Worth re-sweeping periodically — but the current answer is
established, and re-running it hoping for a different result would be
waiting rather than working.

---

### 8. New Zealand GETS — two real items, and a correction

**CORRECTION, 2026-09-02 overnight sweep.** This entry previously said
"36 security/IT keyword matches". That figure was produced by a LOOSE
keyword set including `ICT`, `software`, `data`, `network` and
`technology`. Swept properly against tight security terms:

```
325  open NZ notices
  5  titles contain "secur" at all
  0  are cyber security
```

All five are physical: fire-alarm remediation at two schools, corporate
(guard) security, an enterprise CCTV install, and a poultry biosecurity
grant. The 43 broad matches are payroll, ERP, footpath replacement,
train-door technology and glazing panels.

**New Zealand currently has zero live cyber security tenders.** The
earlier headline was IT-adjacent volume, not demand for your work, and
promoting it as "36 matches" overstated the market.

**What IS real, both confirmed `Required Pre-qualifications: None`:**

| | |
|---|---|
| **NZ Ministry of Defence — Technical Support Services (TSS) Panel Reset 2026** | |
| Closes | **30 September 2026** |
| Type | Notice of Information (Advance Notice), ref `TSS-2026-AN` |
| Pre-qualifications | **None** |
| Categories | Management advisory, professional engineering, technical writing |

A **panel reset** is the rolling-admission structure that fits a solo
operator — and an Advance Notice means the real RFP is still coming, so
there is time to prepare rather than react.

| | |
|---|---|
| **Health NZ — Enterprise Observability Capability and Platform** | |
| Closes | **25 September 2026** |
| Type | Request for Information (market research), ref `RFI26-663` |
| Pre-qualifications | **None** |
| Regions | **International** — explicitly open to non-NZ suppliers |
| Category | Software |

An RFI is low-commitment by design: responding is a legitimate way onto
a buyer's radar with no bid machinery, no consortium, no references.

**Eligibility (unchanged, still verified):** NZ rules *"do not
discriminate against suppliers (domestic or international)"* and reflect
*"the Australia New Zealand Government Procurement Agreement"* and the
WTO GPA. No NZBN or local-presence requirement found across five
procurement.govt.nz pages — absence of evidence, not confirmed absence.

---

### 9. NLnet NGI Zero — €5,000–€50,000, individuals eligible

| | |
|---|---|
| **Value** | €5,000 – €50,000 |
| **Eligibility** | Quoted: *"available to both individuals and organisations of any type"* |
| **Co-contribution** | None found |
| **Call opens** | **2026-09-03 — tomorrow** |
| **Call closes** | 2026-11-03 |

The only grant found that a sole trader with no trading history could
genuinely receive.

---

### 10. Pwn2Own Berlin 2026

| | |
|---|---|
| **Value** | **$20,000 – $250,000 per target** |
| **Registration closes** | 7 May 2026 |
| **Lifetime-earnings gate** | **None** |

**Pwn2Own Ireland is gated:** it requires **$15,000 already earned
through ZDI** before you may compete. Quoted from its own rules. Which
is another reason ZDI is item 1 on this board.

---

### 11. Denmark + Netherlands — two new national boards, now swept automatically

Both national below-threshold boards are reachable and wired into the
hunt as of 2026-09-03. Neither publishes bidder criteria, so nothing
from either can ever come back QUALIFIED — every notice is
`INSUFFICIENT_DATA` until its documents are read. That is the honest
answer, not a defect.

**Denmark — `udbud.dk`.** One live security notice:

| | |
|---|---|
| **Danmarks Nationalbank — cybersecurity advisory framework** | |
| Value | **DKK 9,200,000** (≈ AUD 2.0M) |
| Closes | **2 October 2026** |
| Link | `https://udbud.dk/bekendtgoerelse/f104f4f6-8fc3-4624-b286-6968e40f18d1` |

Also seen this sweep: Statens IT, Managed Detection and Response,
**DKK 24,000,000**, closes **17 September 2026**.

**Netherlands — TenderNed.** 8 live notices, one directly on point:
*Informatiebeveiliging en cybersecurity* (publication 430417). Two SOC/
SIEM tenders from regional safety authorities close 25 and 28 September.

**The blunt caveat on both:** Danish notices are bilingual and the
English half is real, so Denmark is readable. **TenderNed notices are
Dutch-only and the API carries no contract value field at all** — value
UNKNOWN, never zero. Submission language is not stated by either feed,
which for an English-only operator is the whole question. Read one
document before treating either as an opportunity.

**Switzerland is out.** `simap.ch`'s search endpoint was located and
every request is redirected by an anti-bot WAF. Getting in means
defeating a control the operator installed on purpose — same refusal as
AusTender. Recorded as a finding, not a target.

---

## ❌ PNG e-GP (NPC/2026-26) — CLOSED, and worth reading why

The Asia-Pacific sweep surfaced this as the only genuinely live cyber
notice in the region: Papua New Guinea's National Procurement Commission
seeking an Electronic Government Procurement system, scoping
"cybersecurity risk assessment and testing".

The RFP was downloaded and read. It is closed, and three separate
things would have blocked it anyway:

> *"Bidding will be conducted through competitive procurement using a
> Request for Proposals (RFP), a two-envelope system with rated
> criteria, **without prequalification** ... and is open to all eligible
> Bidders."*

**No prequalification** and **open to all eligible bidders** — genuinely
the shape we have been hunting. Then:

| | |
|---|---|
| Deadline | **June 15, 2026, 17:00 PNG time** — passed |
| Bidding document | **non-refundable fee of PGK 5,000** (~AUD 1,900) |
| Submission | **"Electronic Bidding will not be permitted"** — sealed envelopes, physically delivered to Port Moresby |
| Structure | four lots |

An addendum exists (`ADDENDUM-1-NPC-2026-26.pdf`) but is a scanned
image with no extractable text, so whether it moved the date is
**UNKNOWN** — a human could open it in seconds.

**The lesson worth keeping, beyond this one notice.** "Without
prequalification" and "open to all eligible bidders" is exactly the
language this campaign has been searching for — and it still came with a
AUD1,900 document fee and a requirement to physically deliver paper to
another country. **Qualification is not the only barrier.** Access cost
and submission mechanics can close a notice that has no eligibility
criteria at all, and no filter built so far would have caught either.

## THE STAGE BEFORE THE BARRIER EXISTS

Every threshold on this board — €2,600,000 turnover, €13,000,000
employer's liability, three reference contracts — is a **selection
criterion**, and selection criteria only exist once a buyer is running a
competition. Before that, a buyer publishes what they intend to buy, and
there is nothing to qualify for because nothing is being awarded.

UK Contracts Finder exposes this directly: `stages=planning`, the same
live-verified parameter as `stages=tender` (a garbage value returns
HTTP 400, so the server genuinely reads it). Confirmed live 2026-09-03 —
it returns real releases with `status: "planned"` and no `tenderPeriod`,
which is exactly the shape the classifier reads as MARKET_ENGAGEMENT.

`foundation/tender_radar.py::planning_feed_url()` now makes that a
standing capability rather than a one-off query.

### ✅ The qualification bander audited for FALSE disqualifications — 2026-09-05

A false DISQUALIFIED is the worst bug this system can have: it silently
discards a notice Kyle could bid on. Live sweep produced 21
DISQUALIFIED; scrutinised every blocking clause. All correct — non-English
submission (ITA/DEU/FRA/NLD/RON/NOR/DAN), or references/certs/insurance
the operator genuinely lacks. **No false disqualification.** The language
rule computes set-overlap between the notice's `submission-language`
tuple and the operator's languages and disqualifies only on *no overlap*
— so a notice permitting `('ITA','ENG')` correctly passes. Verified the
logic and pinned it: 5 regression tests now guard the multi-language case
(the exact failure mode where a future `any`→`all` change would start
hiding English-biddable notices). The bander is not costing us
opportunities.

### The base rate, measured

Eighteen 30-day windows walked back from 2026-09-03, throttled:

```
444  planning-stage releases scanned
  3  unique cyber-relevant notices
     = 0.7%
```

That is the honest yield of this route on this source. It is thin, and
saying so is worth more than re-running it hoping otherwise. The route
is permanent and costs one request per cycle; it is not a lane to sit
and wait on.

**What the 18 months actually contained:**

| Notice | Buyer | Value | Published |
|---|---|---|---|
| Supply Chain Notice: WP078 Data | Ministry of Defence | **£600,000** | ~Jun 2026 |
| **Cybersecurity Training 2025 to 2029** | Royal Borough of Kingston upon Thames | **£69,552** | ~Jun 2025 |
| CCS Cyber Security Services 3 (DPS) Stage 1 | Metropolitan Police Service | — | ~Nov 2025 |

The Kingston notice is the interesting shape: **£69,552** is small enough
that a solo operator is a plausible supplier, and it is *training* rather
than testing — deliverable by one person, with no SOC to staff round the
clock. It is also from June 2025 and is therefore likely gone; it is
listed as **evidence that councils buy cyber work at this size**, not as
a live target.

The first sweep's three hits were all physical security — Waltham Forest
manned guarding at £5,798,058, MoD supply-chain notice WP073 for CCTV,
access and intruder at £300,000.

### Find a Tender rate-limits

Probing find-tender.service.gov.uk's search for a notice-type filter
returned **HTTP 429** after four requests spaced three seconds apart.
Backed off rather than continuing — that host needs a slower cadence
than Contracts Finder, and UKRI-6251 was reached through its OCDS API
rather than its search page anyway. Recorded so the next sweep does not
rediscover it.

### The Irish register, walked end to end — and what 200 rows was hiding

**2026-09-03.** Every previous Irish sweep read the first 20 pages: 200
of 2,921 open notices, **7%**. Walking all 293 pages took ten minutes at
a two-second courtesy pace and changed the picture completely.

```
2,921  open notices in the register (matches the site's own "2,916")
   87  security-relevant by keyword
   44  deadline already passed  (the register lists stale CFTs)
   20  deadline still open
   23  NO deadline at all -- every one an "Established" DPS or
       Qualification System, the nine cyber ones now Tier 1 item 3
```

The 23 are the finding. A notice with an empty deadline field looked
like missing data; it is the defining property of the one procurement
instrument that never closes, and it was invisible for the whole
campaign because it lives past page 20.

**How the depth was reached — a mistake corrected twice.** eTenders'
sort and pagination parameters were both recorded in this project's own
code as "silently ignored", measured against
`prepareCurrentOpportunities.do`. That page 302-redirects to page 1
whatever you append to it, so both parameters *looked* dead. Pagination
was re-tested against the real endpoint on 2026-09-02 and found to work.
**Sorting was left uncorrected in the same probe** and re-tested only
now — it works too, and works globally across the whole register, which
is what makes a ten-minute walk safe: in the default recency order every
notice published mid-walk shifts rows across a page boundary already
passed, and those rows are lost silently.

`freeText` was re-tested against the correct endpoint as well and is
**genuinely ignored** — a real query and a nonsense query return
byte-identical rows. That one was right.

### A quarter of this system cannot be invoked

**Measured 2026-09-04.** `foundation/` holds 97 modules, 91 with test
files. **23 of those 91 — 25% — were imported by nothing and have no way
to run themselves.** They exist, they are tested, and no production path
reaches them.

```
python3 -m foundation.operator_cli reachability
```

This was found by asking why the same mistake had happened three times
in three days: the Denmark and Netherlands mouths (60 tests, absent from
the source registry), `deep_sweep()` (walked Ireland's whole register,
invocable only from a Python shell), and `spec_crossref` (39 tests, no
caller at all). Each was caught by accident, one cycle late. The
question was how many more there were. Answer: 23.

**Some are deliberate and the report says so.** `publication_gate` guards
`git push`, a human action with no in-repo call path — `CLAUDE.md`
already documents that. The report states plainly that unreachable is a
*fact, not a verdict*, and refuses to guess which ones are intentional.

**But one was not deliberate, and it mattered.** `secret_scanner` was in
the list. This repository is **public on GitHub**, and its own secret
scanner had no automated caller — it ran when someone remembered. Every
"secrets: 0" line on this board came from me invoking it by hand each
cycle. That is a safety control resting on habit.

**RESOLVED 2026-09-04 — the 20 are now classified, and none is a genuine
gap.** "A quarter of the system is unreachable" read as alarm; it isn't.
Each of the 20 was classified from its OWN docstring (checkable, not
asserted) and `operator_cli reachability` now prints the verdict inline:

```
DELIBERATE_GATE 4 · PRIMITIVE 10 · DORMANT_CAPABILITY 6
```

- **4 DELIBERATE_GATE** — `hells_gate`, `publication_gate`,
  `contribution_gate`, `write_scope`: each guards a real external/human
  action (git push, entry to another repo, a write event) that has no
  in-repo call path *by design*. Wiring a caller would FAKE the action.
- **10 PRIMITIVE** — composable building blocks (`low_regret_engine`,
  `reality_yield_ledger`, `regression_engine`, `state_space_mapper`,
  `defusal_router`, `contract_compat`, `admission`, `capability_profiles`,
  `switch_hardener`, `historical_findings`): correctly dormant until a
  real decision supplies their inputs. A CLI feeding them invented inputs
  would be theater — `low_regret_engine` is the clearest: it takes
  caller-declared payoffs, and inventing payoffs for the deals would
  fabricate precision.
- **6 DORMANT_CAPABILITY** — `target_mapping`, `brick_adapter`,
  `gold_brick`, `offer_router`, `queue_worker_adapter`, `autonomous_window`:
  real capabilities whose consumer is a pipeline mode not currently active
  (the commercial-receipt pipeline, the software-demand GitHub→PyPI
  pipeline, the autonomy ramp). `target_mapping` was checked directly —
  its consumer correlates GitHub repos to PyPI/npm packages, and the
  active focus is tenders, which have no package to map.

**The one real operator-facing gap was `situation_analysis`, wired
2026-09-04 (below).** A `test_reachability` forcing function now fails if
any future module becomes unreachable-and-unclassified, so "unreachable,
intent unknown" can never silently return.

**FIXED 2026-09-04. 21 → 20 — `situation_analysis` wired.** The largest
capability in the repository (977 lines: bottleneck / tension / off-ramp
analysis) was reachable from nothing. Wired via `foundation/ops_situation.py`
→ `operator_cli situation`: it builds a real `SituationAnalysis` from the
verified operator facts (profile empty) and the live deals, then lets the
engine COMPUTE the bottleneck from dependency structure. It independently
derives what the close pack asserts by hand — **identity credentials (name/
ABN/address/contact) block all 15 live deals; declared experience blocks 4**
— the engine is never told the answer. 6 tests, honest AMBIGUOUS_MULTIPLE
(the engine refuses to force a single winner when two constraints both score
HIGH, and the rationale shows 15 vs 4 so the reader sees which dominates).

**FIXED 2026-09-04, same night. 23 → 22.** `sentinel.check_high_
confidence_secrets()` now runs on every pulse sweep, which is part of
the standing cycle protocol. It is deliberately **HIGH and MEDIUM only**:
measured across this repository, 6,476 LOW matches (emails, `/home/`
paths) against 9 HIGH/MEDIUM. A check firing 6,476 times is one people
scroll past — which returns the scanner to being ignored, the exact
state it was in. HIGH is real key material (AWS ids, PEM private key
headers); MEDIUM is a credential assignment.

Three things worth knowing about how it was built:

- **A test caught a real bug in the check itself.** The scanner returns
  a *relative* path when given a relative root and an *absolute* one
  otherwise. My allowlist compared raw strings, so it matched in this
  repository and silently never matched anywhere else — an exclusion
  that looked correct and was load-bearing on the caller's working
  directory.
- **The exclusion is one named file**, `test_secret_scanner.py`, not a
  glob. A pattern there could quietly grow to cover a real leak.
- **`test_sentinel.py` is NOT allowlisted**, so its own fixtures are
  assembled at runtime from fragments rather than written as literals.
  Allowlisting a 2,800-line test file to make my own fixtures
  convenient would hide a real leak inside it.

The finding it emits states that a pushed secret is **not reversible** —
deleting the file leaves it in git history, so the action is rotation,
not removal.

Also unreachable, and each named in `CLAUDE.md` as a capability:
`situation_analysis` (977 lines, the largest module here),
`target_mapping`, `reality_yield_ledger`, `corpus_triage`, `admission`,
`hells_gate`, `switch_hardener`.

**Deliberately a report, not a gate.** 23 findings on every sweep is a
check people learn to scroll past — the same call made last cycle when
`spec_crossref`'s unreferenced check produced 27 candidates and all 27
were innocent. It becomes a gate honestly once the number is near zero.
Until then it is a number to drive down, and now it is a number rather
than a memory.

### The green light itself was unreliable, and tonight's work caused it

**Found 2026-09-04 by a regression run that failed and then passed on
identical code.** That had happened twice this evening and been written
off as noise both times. It was not noise.

`foundation/sigil.py::_dimension_proof()` shells out to run each
subsystem's test suite with `timeout=120`. Measured:

```
foundation   128.8s  rc=0  OK (skipped=1)   *** EXCEEDS THE 120s TIMEOUT ***
taal           1.4s  rc=0  OK
rpa            1.4s  rc=0  OK
```

**Seven percent over the limit.** A `TimeoutExpired` sets
`all_green=False`, which caps the PROOF score at `min(4, total // 200)`
instead of the green formula, which fails the `foundation` suite, which
fails `./run_all_tests.sh` — the gate every commit in this session was
checked against. Whether the repository looked green depended on how
loaded the machine was at that instant.

**And this session caused it.** ~200 tests were added tonight across
`entry_gate`, `spec_crossref`, `deep-ireland`, the document readers and
the income fixes. The suite grew across a cliff nobody was watching,
because the limit was the bare literal `timeout=120` inside a
`subprocess.run(...)` call.

Two fixes, and the second matters more:

1. `PROOF_SUBSYSTEM_TIMEOUT_SECONDS = 600` — a named constant at ~4.5×
   the measured duration, so ordinary growth does not re-cross it. Safe
   to raise because the timeout is the *second* net here:
   `recursion_guard.check()` structurally prevents the unbounded forking
   it was originally added to backstop.
2. **A timeout is no longer indistinguishable from a test failure.**
   Both previously produced `all_green=False` and the same degraded
   score, so a suite that was merely slow reported as `FAILURES
   PRESENT` — sending the next reader hunting for a broken test that
   does not exist. It now names the timed-out subsystems and says
   plainly `(not a test failure)`.

Same failure family as everything else this board has recorded in two
days: **a confident verdict computed over an artefact.** This one was
the verdict on all the others.

### Every opportunity now carries what it costs YOU to start

`python3 -m foundation.operator_cli gates <document>`

Every ranking surface in this project sorted by what an opportunity is
worth. None sorted by what it costs to begin — which is why a €175M DPS
sat at the top of this board and the €250k penetration-testing
qualification system that is actually reachable sat underneath it.

**UPGRADED 2026-09-05 — it now sees insurance SOFTNESS, the distinction
that separated the one pursuable Irish lead from the noes.** The tool
used to treat *"must maintain €6.5M cover held"* (RTÉ — a real wall)
identically to *"provide a broker letter that cover can be arranged"*
(GNI) and *"has in place or the ability to obtain"* (HSE) — soft
requirements met by a statement, not by possessing the thing. It now
distinguishes HELD from DECLARATION and ranks accordingly. Re-run on the
five real docs, cheapest-to-start first, matching the hand-analysis:

```
cost  document              hard walls (need you)     satisfiable by a statement
  8   Irish Rail 7289       none                       — (insurance deferred to call-off)
 11   GNI 23/049            tax clearance              INSURANCE (broker letter)
 14   RTÉ 25P041            INSURANCE (held €6.5M)     —
 19   Asiera                — (24×7 SOC is the wall)   tax clearance (has applied)
 21   HSE 22167             — (Ireland-based staff)    INSURANCE (ability to obtain)
```

The `gates` command now prints a distinct section:
*"satisfiable by a STATEMENT, not by holding the thing — a broker
letter, an ability-to-obtain, a willing-to-raise-if-awarded — Kyle can
meet these now."* Verified against all five documents I read by hand;
9 tests pin the HELD-vs-DECLARATION calls with verbatim phrasings.

`foundation/entry_gate.py` computes these columns per document:

- **needs you personally** — registration, legal entity, identity
  verification, certification, insurance HELD, entry fee. Nothing you
  build closes these.
- **closable by work or partnering** — turnover, references, local
  presence, round-the-clock staffing.
- **deferred by the document itself** — requirements the buyer's own
  words push past admission.

That third column is the one worth having, and it is exactly the
distinction two cycles of hand-reading produced: RTÉ and Irish Rail make
the **identical** insurance demand, and one is a Pass/Fail gate at
admission while the other applies only once you have been selected to
call-off. A tool reporting both as "insurance required" throws away the
difference between a wall and a later errand.

**Run across all six Irish documents, cheapest-to-start first:**

```
cost   chars     document                        needs you to start
  8   136,017   Irish Rail 7162 ICT consultancy   NONE
  8   129,864   Irish Rail 7289 penetration test  NONE
 14    68,315   RTÉ 25P041 cyber DPS              INSURANCE
 15     7,569   Asiera Part B  (FRAGMENT)         NONE — see caution
 16    80,458   Gas Networks Ireland 23/049       INSURANCE, TAX CLEARANCE
 26    70,187   HSE 22167 unified cyber IR        INSURANCE
```

That order is the one this board reached by hand over two cycles. It is
now computed, so the next sweep cannot quietly revert to sorting by
contract value.

**It got the answer backwards first, and that is recorded on purpose.**
The first version weighted by *who must act* alone and put Asiera at the
top as the cheapest thing on the board — Asiera, which demands a
**24×7×365 staffed Security Operations Centre**. Weighting a
round-the-clock service the same as a turnover figure, because neither
needs a signature, is how the least reachable opportunity in Ireland
became the recommendation. Four more defects came out of testing against
documents whose verdicts were already known by hand:

- `company registration number` matched the **applicant-details form
  field** every PQQ carries — a question asking who you are, read as a
  requirement to be a company.
- `ISO 27001` matched RTÉ **describing the services it wants to buy**,
  and `ISO 9001` matched a scored question you may answer "no" to. Same
  class as the TED sweep matching "Market research services" as market
  engagement when it was the service being procured.
- RTÉ's Pass/Fail insurance table was read as **deferred**, because an
  unrelated tax-clearance sentence sat inside the staging window —
  inverting the one distinction the module exists to make. Admission
  evidence now beats deferral evidence.
- Irish Rail's insurance clause was **not detected at all**: its PQQs
  name no policy type, only "the insurance requirements of the
  Contract". A gate the tool cannot see cannot be reported as deferred,
  and being deferred is the entire finding for those three documents.

**And the fragment problem, which is not fixed and is instead labelled.**
Asiera's Part B is 7,569 characters of a multi-file pack. It scored
cheap because most of its requirements live in files the assessment
never saw. Entry cost is comparable only between comparably complete
reads, so every assessment carries `chars_read` and anything under
20,000 characters prints a CAUTION. A low score on a fragment means an
unread pack, not an open door.

### The full-register walk is now a command, not a script

`python3 -m foundation.operator_cli deep-ireland` — dry-run by default,
`--live` to walk. It states the time cost before you commit (~293
requests, ~10 minutes), labels an empty deadline as
`NO CLOSING DATE (rolling admission)` rather than printing a gap, and
**refuses to present a truncated walk as a whole one**: a walk stopped
by budget, page cap or a dropped connection prints a warning that the
results are a prefix of the register, so an absence in them is never
read as an absence in Ireland.

It was built last cycle and reachable only from a Python shell — the
same unwired shape as the Denmark and Netherlands mouths that sat
outside the source registry for a cycle. A capability nobody can invoke
is not a capability.

### Two document readers were returning markup, not words

Found by trying to read the Irish criteria above and getting rubbish.

**`.docx`** — the paragraph split matched `<w:p[ >]`, which consumes the
`<` and one character, leaving the rest of the opening tag
(`w14:paraId="672A6659" w:rsidR="006D172B" ...>`) as ordinary text that
the following tag-strip can no longer match. RTÉ's real DPS document
came out as **191,868 characters** opening with `w14:paraId=`. Fixed by
splitting on the closing tag, which has no attributes.

**`.rtf`** — Irish Rail serves its qualification documents as RTF, a
format the reader did not handle at all. It fell through to the
plain-text branch and returned **2.7 million characters** of
`\rtlch\fcs1\af0\afs20` control words. Now parsed properly: 129,204
characters of readable English, which is how the criteria above were
found. Font and style tables are dropped whole — their contents are
typeface names indistinguishable from prose once the markup is gone.

The magic-byte check that was supposed to catch this read **four** bytes.
`{\rtf` is five. The detection could never have fired.

Both are the same failure this project keeps meeting: **confident output
computed over noise.** The access-barrier scanner was reading markup and
reporting NONE_DETECTED on it.

### A defect that made every sweep look busier than it was

**Found 2026-09-03 in the live sweep run for this cycle.** The hunt
assessed 120 notices; **100 of them were published in 2016 and 2017.**
Nothing was broken and nothing raised — the CLI simply never bounded TED
by date, so each sweep spent its whole budget re-reading and re-banding
notices that closed years ago, and printed them as findings.

Fixed: the TED query now carries `publication-date >= today(-365)` by
default. The honest caveat, recorded in the code: publication date is a
**proxy**. `deadline-receipt-request >= today()` is the filter that
actually means "still accepting tenders", and it measures **zero
results** when combined with the full-text clause a keyword hunt needs.
A notice published inside the window may still have closed.

---

## 🤝 THE DELIVERY-PARTNER LAYER — first slice built 2026-09-05

Every real opportunity on this board is gated on something Kyle lacks:
held insurance, a certification, corporate references, a turnover figure,
staff based in a jurisdiction. The lawful way to clear those is a
**delivery partner** who supplies the missing capability, with revenue
shared under a transparent agreement. The single highest-leverage missing
piece was the **bridge** from "this opportunity has a gate Kyle can't
clear" to "what a partner must supply" — and a way to hold candidate
partners honestly. That bridge is now built (`foundation/partner_network.py`,
`operator_cli partner-needs <document>`), reusing `entry_gate` — it
invents no requirement the document did not state.

Run against the board's real leads, it computes the partner shape of each:

| Opportunity | What a partner must supply |
|---|---|
| **Irish Rail 7289** | REFERENCES + MINIMUM_TURNOVER (€250k — the PQQ's own reliance route) |
| **RTÉ 25P041** | INSURANCE (held €6.5M) + REFERENCES + TURNOVER |
| **HSE 22167** | LOCAL_PRESENCE + STAFFED_ROUND_THE_CLOCK — an **Ireland-based MSP** partner, the one wall Kyle cannot clear alone |

**What this slice deliberately is, and is not.** It is the data model +
the opportunity→need bridge + a forward-only lifecycle
(DISCOVERED → … → ACTIVE) with the discipline that **a contact is never a
partner** (`is_partner()` is true only for a signed ACTIVE relationship;
DISCOVERED/CONTACTED never are) and **a claim is never fact because the
candidate said it** (evidence tiers: SELF_REPORTED cannot become VERIFIED
without an independent source). It has **no outreach, no email, no
network, and no invented people** — the registry starts empty and every
test is synthetic. Outreach, agreements, and payments are human-approved
actions gated elsewhere; automation prepares and ranks, it never invents
authority or consent. 37 tests, the adversarial set (fabricated
credentials refused, AI-confidence state-skip refused, opt-out respected).

**Kyle's move this unlocks:** the HSE €16M–€60M cyber systems, written off
as "geography wall, impossible for a solo operator," are now precisely a
**find-an-Ireland-based-security-partner** problem — a real, lawful
commercial path, not a dead end. But no partner exists yet: the next step
is discovering evidence-backed candidates, which needs Kyle's go-ahead on
outreach.

## THE MECHANISM THAT CHANGES THE STRATEGY

Found 2026-09-02 by reading **all five** live Irish tender documents in
full. **All five carry it**, in the buyers' own words, and one puts a
**checkbox** on the form for it. This is not a quirk of one buyer — it
is how Irish public procurement is written.

**You do not have to meet the selection criteria yourself.**

Health & Safety Authority RFT, §3.1:

> *"Tenderers should note that where a Tenderer is relying on the
> capacity of other entities (for example, Subcontractors) for the
> purposes of fulfilling any of the Selection Criteria..."*

An Post SOC/SIEM PQQ — a tickbox on the form itself:

> *"Tick to confirm if Applicant is relying on combined turnover of
> consortium members or those of any other persons/entities, in order to
> meet the minimum financial qualification..."*

Fáilte Ireland PQQ, Section A:

> *"NOTE #1: in the case of the Candidate being a grouping, the condition
> at (i) above may be satisfied by the group members as a whole."*

And the same PQQ, on how capability is assessed:

> *"Candidates should distinguish between capabilities delivered directly
> by the Candidate and those delivered by consortium members or
> subcontractors."*

### What this actually means

Every EU tender on this board demanded turnover you do not have,
insurance you do not carry, and reference contracts you have never held.
The conclusion drawn all campaign was "these are structurally out of
reach."

That conclusion was about **bidding as the prime**. The rules explicitly
provide for a different position: the specialist whose capacity a prime
**relies on**. The buyer does not merely tolerate this — the PQQ has a
dedicated field for it and requires the prime to name who delivers what.

So the honest reframing:

| | |
|---|---|
| **Wrong question** | "How do I reach €1,800,000 turnover?" |
| **Right question** | "Which prime bidding this contract needs a tester, and how do I become the named specialist in their submission?" |

That is not a lesser path. It is the position the procurement framework
was written to accommodate, and it needs no turnover, no insurance of
your own, and no corporate reference history — the prime carries those.

### What it does NOT mean

It does not make you eligible alone. The insurance and reference bars
still apply to the grouping as a whole, and the prime still has to want
you. It also does not bypass anything: the ESPD must be completed for
every consortium member and every subcontractor whose capacity is relied
on, so you are declared, visible, and accountable in the submission.

### Why this outranks everything else found tonight

`SUBCONTRACT_TARGETS.md` and `SUBCONTRACT_APPROACH_PACK.md` were built
as a fallback lane — what to do because the tenders were closed. This
promotes that lane from consolation to **the mechanism the buyers
themselves specify**. Pulse Security, Volkis, INFODAS and AWARE7 stop
being "firms that might give you work" and become "firms whose bids
have a slot with your name on it."

**ACTION:** when approaching any firm on that list, the offer is not
"do you have spare work." It is "I am available as named specialist
capacity for tenders you are bidding." That is a different conversation,
and it is the one the documents say buyers expect to see.

---

## MARKET ENGAGEMENT — the notice type with no qualification at all

Found 2026-09-03. A **preliminary market engagement** notice (UK) or a
**Request for Information** (NZ, Ireland) is a buyer asking the market
what is possible, BEFORE writing a tender. Responding to one requires no
turnover, no insurance, no references, no certifications — because
nothing is being awarded yet.

It is the only public-sector notice type a solo operator can answer on
equal terms with a consultancy, and it puts you in front of the buyer
while the requirement is still being shaped.

| | |
|---|---|
| **UKRI-6251 — Cyber Security, Managed Service, Detection & Response, SOC** | |
| Buyer | UK Research & Innovation |
| Type | **Preliminary market engagement notice (UK2)** |
| Notice | 2026/S 000-080084, published 21 Aug 2026 |
| Scope | *"A Cyber Security provider to deliver collaborative SOC services, working with the existing STFC cyber security team"* |
| Stated qualification requirements | **None** |
| URL | find-tender.service.gov.uk/procurement/ocds-h6vhtk-06e9f0 |

Note the word **collaborative**, and *"working with the existing STFC
cyber security team"*. That is a buyer describing augmentation of their
own team, not replacement of it — which is the shape that fits a
specialist rather than a managed-service prime.

**Deadline UNKNOWN** — not published on the notice page. Needs a human
to open it or contact the buyer.

Also in this class, already on the board:

- **Health NZ — Enterprise Observability**, RFI, closes 25 Sep, regions
  International, `Required Pre-qualifications: None`
- **NZ Ministry of Defence — TSS Panel Reset**, Advance Notice, closes
  30 Sep, `Required Pre-qualifications: None`

**Three live notices where the barrier is zero.** After five Irish
documents proved the tender lane is closed at €400k–€2.6M turnover, this
is the class worth watching — and no sweep before tonight distinguished
it from ordinary tenders.

---

## TIER 3 — no credential gate, results-paid, slow

### 11. Bug bounty

| Program | Range | Platform |
|---|---|---|
| Adobe Public | $75 – $15,000 | Intigriti |
| NVIDIA Public | $150 – $15,000 | Intigriti |
| ICI PARIS XL | $10 – $8,500 | Intigriti |
| The Perfume Shop | $10 – $8,500 | Intigriti |
| Marionnaud | $10 – $8,500 | Intigriti |
| Coveo | $100 – $5,500 | Intigriti (2FA) |

**The three retail programs are one org — AS Watson Group.** Same reward
table, same exclusions, three separately-scoped brands. One methodology,
three payable programs. **Ranked ABOVE Adobe for a newcomer**, because
Adobe's platform migration reset the *platform*, not a decade of
picked-over application code.

**Rate limit:** The Perfume Shop's brief states a hard **5 req/s** cap.
Apply it to all three AS Watson brands.

**Payment gates — paperwork, not credentials.** Intigriti: ID
verification for KYC, sole traders explicitly supported as natural
persons. HackerOne: tax form, Veriff identity check, payment method.

**Sequencing trap worth knowing before you hit it:** HackerOne's ID check
unlocks **after** your first report; Intigriti's blocks payout if done
**before**. Same task, opposite order, weeks lost if you get it wrong.

**The honest economics, from HackerOne's own data:** the top 100
researchers took **39% of one year's $81M**. Newcomer duplicate rates
50–80%. No platform publishes a time-to-first-bounty figure. **Budget
three to six months of near-zero income.**

**Seventeen of Intigriti's 24 programs are VDPs** — responsible
disclosure, no money. A long program list is not a long paying list.

---

### 12. Pentest-as-a-service — skills tests, not certificates

| Platform | Gate | Verdict |
|---|---|---|
| **Synack Red Team** | Private CTF on HackTheBox | **Certifications explicitly optional.** Best fit |
| **Cobalt Core** | Same logic, tougher de facto bar | Second |
| Intigriti Hybrid | Requires 1yr bug-bounty track record first | Later |
| **HackerOne Pentests** | 3 years + named certs (OSCP/OSEP/OSWE) | **Hard no** |
| Bugcrowd Pentests | Page could not be fetched | **UNRESOLVED — not researched** |

**Synack vetting takes ~6 months.** Start it now so it is running in the
background while other lanes produce.

**✅ NOW IN THE DIGEST ROSTER — 2026-09-03.** Synack was researched here
but never surfaced in the phone digest Kyle actually uses — a real
finish-the-door gap. Re-verified live (synack.com/red-team reachable,
robots permits it, "skills assessment" throughout, certifications count 0)
and added as a PURSUE card (Cobalt named as the parallel apply). **This is
the single best profile fit on the board:** paid pentest work gated on a
skills test in Kyle's own stated domain, with no certs / insurance /
references / turnover — the exact walls that killed every tender. The
honest caveat carried on the card: the assessment is real skill, not
form-filling.

---

### 13. Subcontracting — firms that win this work and take individuals

| Firm | Country | Gate | Note |
|---|---|---|---|
| **Pulse Security** | NZ | **No CV gate, no cert requirement** | Work samples substitute. Lowest friction found |
| **Volkis** | Sydney | Ran an associate-tester program for varying experience levels | Confirmed from a staff member's own published bio. **Site 403s to my fetcher — check it in a normal browser** |
| **Airglow Security** | AU | Explicit no-certification, capability-first | |
| **Vertex Cyber Security** | AU | Same | |
| **AWARE7** | Germany | ~30 staff, publicly solicits pentester applications | Careers URL moved to `a7.de/career/` |
| **INFODAS** | Germany | 3 TED wins, "Security Testing" track confirmed | Vacancies page empty at last fetch |

**Correction carried forward:** **OnSecurity has no "Associate Network"
and no OSCP/OSWE/CREST requirement** anywhere on its own live pages. That
bar came from a third-party aggregator and we had recorded it as fact.
They are currently not recruiting.

---

## CLOSED — stop paying attention to these

Each was investigated and eliminated with evidence. Recorded so nobody
re-chases them.

| Target | Why it's dead |
|---|---|
| **TED 578580-2026 degewo** | `Ausschlusskriterien`: 3 testers + 2× €50k corporate refs + €3M insurance + CEFR C1 German |
| **TED 244223-2024 ECHA** | €1,000,000 average turnover + 5× €100k references. **I reported this as QUALIFIED and was wrong** |
| **RTÉ 25P041 (Ireland)** | Turnover ≥€350k/yr × 3yrs, PL €6.5M, Cyber €1M, Professional €1M, Employer's €13M. All Pass/Fail |
| **NHS England £7.2M** | Real, but `procurementMethod: selective` via CCS RM3764 DPS. Needs prior DPS admission |
| **EU DG DIGIT 773405-2024** | It's a **hardware** DPS — "end-user IT hardware equipment". An earlier pass inferred services from the title alone |
| **UK Space Agency** | EoI closed 1 Oct 2025 |
| **UK sub-threshold band** | 60-day sweep, 975 releases, 62 open, **0** that were open + under £30k + security |
| **AusTender** | Every route WAF-blocked. OCP mirror holds 50,269 records, **0** with a tenderPeriod — all awarded |
| **CanadaBuys** | Best data found anywhere (966 open, 867 future-dated) — robots.txt names bingbot/Googlebot then disallows everyone else. **You can download the CSV in a browser; my crawler won't** |
| **World Bank** | 417k records, **0** currently open. Date filters silently ignored |
| **Singapore GeBIZ** | Award-only, and foreign suppliers need a Singapore-incorporated entity |
| **SAM.gov (US)** | Requires US entity registration (UEI/NCAGE) |
| **Victoria eServices** | $5,000,000 public liability insurance |
| **SA Government bug bounty** | Press reported "financial rewards"; the official page says they do **not** compensate |
| **R&D Tax Incentive** | Restricted by statute to body corporates. Sole traders categorically excluded |
| **Industry Growth / Ignite Ideas** | Matched co-funding required — disqualifying with no capital |

---

## THE THINGS ONLY YOU CAN DO

Twelve facts across four schemes, and none of them can be generated:

```
ABN                              → NSW, ICN
Declared service skills          → NSW, CCS DPS, ICN, QLD
Two referee reports              → NSW          ← the one open question
Supplier Declaration signature   → NSW
Financial solvency confirmation  → NSW
DPS Schedule 1 filter selection  → CCS DPS
SQ financial details             → CCS DPS
Supply categories                → QLD
Business info / service regions  → QLD
```

The dossier generator fills what is known and writes
`UNKNOWN — VERIFICATION REQUIRED` everywhere else. It **cannot** invent
an ABN, ACN, licence, insurance figure, certification, customer or
referee — a test asserts no 9+ digit run appears anywhere in an empty
profile's output. These forms carry legal declarations you sign.

---

## COSTS, so nothing is a surprise

| Item | Cost | Source |
|---|---|---|
| Professional indemnity, sole trader IT consultant | **from $43/month** | BizCover, April 2025 |
| PI + public liability combined | **~$81/month average** | BizCover, April 2025 |
| **$5M PL specifically (what NSW wants at contract time)** | **UNKNOWN** | Nothing found priced at that limit — needs a broker quote |
| NSW scheme application | Free | |
| ZDI registration | Free | |
| ICN Gateway discoverability | ~$600–$1,480/yr (low confidence) | |

---

## THE LEGAL QUESTION, unresolved

**Does an individual need a licence to sell penetration testing in
Queensland?**

Verdict recorded: **UNCLEAR, LEANING NO.** The Federal Register of
Legislation was confirmed live to have no Commonwealth pentesting
licensing instrument. The Queensland Security Providers Act 1993 text
could not be fetched (every URL 404'd), and Queensland's Act is
generally understood to cover *physical* security rather than IT
security testing — but that was not confirmed from the source.

**Get the Queensland Office of Fair Trading's answer in writing before
selling pentesting under that name.** This is the only item on this
board with legal exposure attached, and it is cheap to close.

---

## CHECK A TENDER DOCUMENT BEFORE YOU SPEND ANYTHING ON IT

```sh
python3 -m foundation.operator_cli access path/to/tender.pdf
```

Reads a `.pdf`, `.docx` or text tender pack and reports the barriers
that have **nothing to do with whether you qualify**: document fees,
paper-only submission, mandatory site visits, local-entity
requirements, bid bonds.

PNG's NPC/2026-26 is why this exists. Its own words were *"without
prequalification ... open to all eligible Bidders"* — zero eligibility
criteria — and it was still unreachable behind a **PGK 5,000
non-refundable document fee** and *"Electronic Bidding will not be
permitted"*. Every other filter here scored it as promising.

Run it on anything before paying a document fee or booking travel.

**What it will not do:** an unreadable document (a scanned image, which
PNG's own addendum is) reports `NOT_ASSESSED`, never `NONE_DETECTED`.
Nothing extractable and nothing to find look identical from inside a
text scanner, and it says so rather than implying a clean result.

---

## RUN THE SYSTEM

```sh
python3 -m foundation.operator_cli brief --live     # what needs you today
python3 -m foundation.operator_cli income --live    # new bounty programs, gigs
python3 -m foundation.operator_cli dossier          # your paperwork + what's missing
python3 -m foundation.scheduled_brief               # one cron-safe run
```

Sources swept: TED (EU), NZ GETS, UK Contracts Finder, UK Find a Tender,
Ireland eTenders.

Bands mean exactly this and nothing more:
- **QUALIFIED** — no *published* criterion blocks you. Criteria held
  back in the procurement documents still can.
- **INSUFFICIENT_DATA** — the notice does not publish enough to decide.
  **Unresolved, not promising.**
- **DISQUALIFIED** — a published clause blocks you, and the clause is
  quoted so you can check it and disagree.

---

## IF YOU DO FOUR THINGS

1. **Open the Bradford portal in a browser.** 11 days, £300,327, and one
   unanswered question that a human session resolves in ten minutes.
2. **Register with ZDI.** Free, no deadline, no gate, and it is the
   prerequisite for the six-figure prizes.
3. **Email NSW about referees.** One email unlocks a $150,000 ceiling.
4. **Finish ICN Gateway.** No reference gate at all — the one you can
   complete today without waiting on anyone.

Then, when those are moving: the **NZ Ministry of Defence TSS Panel
Reset** (30 Sep, pre-qualifications None) and the **Health NZ
Observability RFI** (25 Sep, International, pre-qualifications None).
Both are low-commitment ways onto a buyer's list.

---

## SWEEP LOG — 2026-09-03

Re-ran `sources_for_query()` + `hunt_multi()` across all five sources
(TED, NZ_GETS, UK_CONTRACTS_FINDER, UK_FIND_A_TENDER, ETENDERS_IE)
against four keywords ("cyber security", "penetration testing",
"security testing", "security"), TED bounded to the last 30 days via
`with_recency()`. Also ran `tender_radar.planning_feed_url()` for the
UK pre-tender (planning-stage) feed directly. `operator_profile.json`
does not exist at the repo root — this run classified notices only
(title/buyer/value/deadline/notice class), which does not depend on the
real operator's facts; no EXAMPLE-profile band verdict is asserted as
real qualification here.

**Fetched (raw, deduped across keyword passes):** 1,520 items touched,
125 unique notices actually reached assessment (TED 75, NZ_GETS 30,
UK_FIND_A_TENDER 20). UK_CONTRACTS_FINDER (5 raw open-status items this
cycle) and ETENDERS_IE (10 raw items) matched none of the four keywords
client-side — a real zero, not a fetch failure (no `SOURCE FAILED` in
either run's skip list).

**Planning-stage feed (UK Contracts Finder, `stages=planning`):**
0 items. A genuinely empty pre-tender sweep this cycle, not an error.

**New MARKET_ENGAGEMENT / ROLLING_ADMISSION notices found:** the NZ
Government Marketplace standing invitation (id 33732411) and the NZ
Defence TSS Panel Reset (id 33830698) both resurfaced — both already on
this board, nothing new there. Two more NZ_GETS RFIs from Ministry of
Defence matched the broad "security" keyword client-side —
**Persistent Surveillance (Air) Phase 1** (id 34593228) and
**Supplier Data Directory Service** (id 34758151) — read and confirmed
**not relevant** to a cyber security / penetration-testing capability
(drone surveillance and a supplier-directory service respectively).
Logged here, not added to the pipeline.

**New COMPETITIVE notices found, none actionable:** an Ireland IT
services RFT (554895-2026, EUR180,000, closed 2026-08-28 — already past
deadline), an Ireland educational-software services contract
(560033-2026, EUR335,917, cyber-irrelevant), and four NZ_GETS RFPs/RFTs
(MOSP 2027, two Fire & Security fire-alarm-remediation contracts,
Pacific renewable-energy scoping, interactive-tool replacement) — all
read and confirmed out of scope.

**New TED notices found, genuinely cyber-relevant, genuinely new, not
on this board — but flagged as likely out of reach on scale, not
added to the pipeline without a value check:**

| Notice | Buyer | Value | Deadline |
|---|---|---|---|
| [Poland — SOC (Security Operations Center) service](https://ted.europa.eu/en/notice/-/detail/545435-2026) | Ministerstwo Aktywów Państwowych | 1,491,951.90 PLN | UNKNOWN — not published in the feed item |
| [Austria — Cyber Security und SOC Dienstleistungen](https://ted.europa.eu/en/notice/-/detail/604199-2026) | Umweltbundesamt GmbH | 7,200,000 EUR | UNKNOWN — not published in the feed item |
| [Belgium — Cyber Security](https://ted.europa.eu/en/notice/-/detail/605935-2026) | Opdrachtencentrale vzw | 35,000,000 EUR | UNKNOWN — not published in the feed item |

All three are UNKNOWN notice class (title didn't match any of
`classify_notice()`'s four pattern sets; this does not mean they are
not tenders — TED's own procedure-type field was not read by this
extraction pass). All three publish only a total contract value, no
per-supplier turnover/insurance/reference threshold in the fields this
sweep read — same "unresolved, not promising" caveat as everything else
INSUFFICIENT_DATA on this board. Given the five-Irish-document finding
(EUR400,000–2,600,000 turnover typically required in the competitive
lane) and these three contracts running 5–200x that ceiling, they are
logged here for completeness, not added to the deal pipeline — opening
the actual procurement documents is the next step if you want to check,
not something this sweep fabricates a verdict on.

**UKRI-6251** (Cyber Security Managed Service / SOC, UK_FIND_A_TENDER)
resurfaced under this cycle's keywords — already on this board and in
the pipeline (deal_id `ukri-6251`), nothing new there.

**Deadlines checked against today, 2026-09-03:** only **Bradford (14
Sep)** falls inside the 14-day window — 11 days out. Fáilte Ireland (24
Sep, 21 days), Health NZ RFI (25 Sep, 22 days), Oireachtas (28 Sep, 25
days), An Post (29 Sep, 26 days), NZ Defence TSS (30 Sep, 27 days),
Dept of Justice (2 Oct, 29 days) and HSA (12 Oct, 39 days) all remain
outside the window.

**Pipeline:** no new deal events appended this cycle — every notice
found was either already tracked or read and confirmed not relevant/not
actionable. `foundation/deal_pipeline_log.jsonl` is unchanged.
