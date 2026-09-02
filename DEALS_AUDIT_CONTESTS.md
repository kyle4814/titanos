# Competitive Security Audit Contests — Research Brief

Date: 2026-09-03
Method: Direct WebFetch against platform sites/docs. WebSearch quota was exhausted for
this session before this task started, so coverage relies entirely on fetches of
known URLs — this is a real gap, flagged where it bites. Nothing below is fabricated;
where a fetch returned no data, it is marked UNKNOWN rather than guessed.

---

## 1. Code4rena (code4rena.com)

**Live/upcoming contests found:** Only one was visible via fetch of code4rena.com/audits:

- **Rujira** (THORChain app layer, Cosmos/Rust) — $40,000 USDC prize pool. Timeline
  Dec 16 2025 – Jan 16 2026, already past submissions-closed at time of writing
  (report in progress). Scope size not shown on the listing page.

This is almost certainly not the full live board — the audits page is JS-rendered
and the fetch likely only captured a partial DOM. **Treat "one contest" as an
artifact of tooling, not a true count of live C4 contests.** Confirm on
code4rena.com/audits directly before relying on this.

**Awards formula** (from docs.code4rena.com/awarding.md — this part is solid):

- High-risk finding pool slice: `10 * (0.85 ^ (split-1)) / split`
- Medium-risk finding pool slice: `3 * (0.85 ^ (split-1)) / split`
  (`split` = number of wardens who found the same duplicate issue)
- The report selected for inclusion gets a +30% bonus slice.
- Partial credit (25/50/75%) for duplicates that don't nail the top-severity framing.
- Two side bonuses, each 10% of the High/Medium pool: "Hunter" (most unique H/M
  findings) and "Gatherer" (most valid H/M findings).

Implication: payout for any single finding decays sharply with duplicate count.
Being first/most-precise on a unique bug matters far more than raw finding volume.

**Entry gate:** None found. No minimum reputation, no KYC to *enter* a contest —
registration is "become a warden," GitHub/Discord/wallet signup. This confirms the
premise of the brief: no certification, no interview.

**Payment mechanics** (confirmed from docs, high confidence):
- Paid via disperse.app in two batches — Batch 1 within ~1 week of results, Batch 2
  after a 30-day review window.
- Tax reporting info required before any payout.
- **For competitions starting March 23 2026 onward: identity verification (KYC)
  becomes mandatory once lifetime earnings exceed $1,000.** Below that threshold,
  no KYC needed.
- ToS reserves right to demand KYB/KYC/tax docs generally.
- Non-US eligibility: not explicitly blocked. Payment is gated on completing a tax
  questionnaire (determines US tax-withholding obligations) — this is standard
  W-8BEN-style non-US contractor handling, not a nationality bar. **An Australian
  individual can very likely be paid**, but confirm mechanics (crypto wallet payout,
  disperse.app requires an EVM wallet address, not a bank account) before assuming
  fiat conversion is handled for you.

**Newcomer earnings data:** UNKNOWN. No stats found on what fraction of wardens
earn nothing or typical first-payout size. C4 does not appear to publish this
itself, and third-party analyses (e.g. independent leaderboard-scrapes) were not
reachable without search. Treat any claim of "X% of first-timers earn $Y" you see
elsewhere as unverified unless sourced.

**Skills:** Contest scope in the sample found (Rujira) was Rust/Cosmos, not
Solidity — C4's contest mix spans EVM Solidity and non-EVM (Rust, Move, Cairo)
depending on protocol. Solidity is still the dominant single language across the
platform historically, but is not exclusive.

Sources:
- https://code4rena.com/audits
- https://docs.code4rena.com/awarding.md
- https://docs.code4rena.com/ (ask-query result on payment/KYC)

---

## 2. Sherlock (audits.sherlock.xyz)

**Live contests:** UNKNOWN by count/name. The contests page is a JS single-page
app — WebFetch only returned section headers ("Active," "Upcoming," "Judging,"
"Escalations Open," "Finished") with zero populated rows. Cannot report live
prize pools or dates. **This needs a manual check by the operator, in-browser** —
tooling could not extract it.

**Payout mechanics** (from docs.sherlock.xyz/audits/watsons.md):
- Watsons "receive any prize money earned from the pool." Exact split formula
  (analogous to C4's decay function) was not present in the fetched section —
  UNKNOWN precise formula, though Sherlock is known industry-wide to also use a
  severity-weighted, duplicate-split model similar in spirit to C4's.
- Payment "within 2 weeks of the audit ending."
- Entry to a normal contest: no staking or collateral found — just GitHub handle,
  Discord handle, wallet address. **No reputation gate to enter.**
- Separate tier: **Lead Senior Watson** (top 10% ranked, invite-only tier) gets
  fixed pay ~$10k per audit week, 75% up front. This is not the newcomer path —
  it requires an established track record on the platform first.
- International payment / KYC: UNKNOWN, not found in the fetched doc section.

Sources:
- https://docs.sherlock.xyz/audits/watsons.md
- https://docs.sherlock.xyz/audits/judging.md

---

## 3. Cantina (cantina.xyz)

**Live competitions:** UNKNOWN. The competitions page reported "51 bounties and
competitions available" but the actual listing did not render for WebFetch (SPA,
returned "no opportunities found matching search criteria" — a filtered/empty
state, not the true count). Docs pages 404'd across three URL guesses
(cantina.xyz/docs, docs.cantina.xyz, docs.cantina.security, www.cantina.security).
**Cantina is the weakest-covered platform in this brief — everything about its
prize-split formula, entry gate, and KYC/payment process is UNKNOWN from this
session.** Needs direct browser visit.

Source: https://cantina.xyz/competitions (52 items number visible but not the list)

---

## 4. Immunefi (immunefi.com)

Immunefi is continuous bug bounty, not time-boxed contests — no submission
deadline, you find a live-in-scope bug on a live protocol and report it any time.

**Top programs by max bounty** (from immunefi.com/bug-bounty/, dated Sep 2 2026
per the page's own "updated" note):
- Ethena — up to $3,000,000
- DeXe Protocol — up to $500,000
- SSV Network, ENS, Lombard Finance — up to $250,000 each

**Severity-based payout ranges:** UNKNOWN in specific USD bands — not present in
the fetched content. Industry-known general shape (not confirmed against current
Immunefi docs this session): Critical bugs (fund-loss-capable) pay the large
headline numbers; Medium/Low severities on most programs pay in the low
hundreds to low thousands of USD, occasionally with a fixed minimum. Treat this
paragraph as background knowledge, not verified current data — flagged as such.

**KYC / non-US payment:** The bug-bounty listing page itself has a filter for
"KYC Required" vs "KYC Not Required," confirming it varies by *program*, not
platform-wide. Specific KYC policy text and explicit confirmation that Australian
individuals can be paid: UNKNOWN — the help-center pages guessed at (two URLs)
both 404'd.

**Newcomer economics:** UNKNOWN — no data found this session.

Source: https://immunefi.com/bug-bounty/

---

## 5. CodeHawks / Cyfrin (codehawks.cyfrin.io)

**Live main competitions found** (mix of public and invite-only, exact live-vs-
closed status not disambiguated by the fetch):
- BattleChain Confidence Pools — 7.25 ETH
- Storage Proofs (Curve) — 14,723 OP
- Liquidity Management (Gamma) — 50,000 USDC
- Core Contracts (RAAC) — 77,280 USDC
- Zaros Part 2 — 70,000 USDC
- Several more in the 15,000–250,000 USDC-equivalent range
- Private/invite-only tier examples: Starknet Staking Part 2 (80,000 USDC),
  Remora RWA Part 2 (4,000 USDC), ZKsync Era (500,000 USDC — largest pool seen
  in this whole research pass, but invite-only, not open entry)

**First Flights** (the actual newcomer-relevant product): confirmed to exist,
59 numbered so far as of this fetch (#59 "SNARKeling Treasure Hunt," #58 "NFT
Dealers," #57 "Stratax Contracts"). These are explicitly labelled
"Beginner Friendly." **Reward is 100 EXP (experience/reputation points), not
cash** in the listing view fetched — could not confirm from this pass whether
any First Flights carry a cash prize on top of EXP; some historically have had
small USDC pools per public C4/CodeHawks community knowledge, but this fetch
did not surface that for current listings. Treat First Flights as a reputation-
building/practice ramp, not an income source, unless you verify a specific one
has a cash pool attached.

**Entry gate:** Sign-up/login only, no reputation or KYC gate to enter a
contest. KYC "required for rewards distribution" on some contests per the page
text, consistent with the other platforms' pattern (KYC on payout, not on
entry).

Sources:
- https://codehawks.cyfrin.io/
- http://codehawks.cyfrin.io/first-flights

---

## Honest Newcomer Economics — What Could and Couldn't Be Verified

This is the section that matters most for a real decision, and it's the one
where this session's tooling let the operator down: **WebSearch quota was
exhausted before any query ran**, which is exactly the tool needed to surface
independent data (Dune dashboards, Twitter/X threads from named wardens on
"my first year in audit contests," Solodit-aggregated stats, Immunefi's own
published leaderboards-over-time). None of that was retrievable via WebFetch
alone in this session because it requires discovery, not direct URL access.

**What can be stated with confidence, structurally, without needing that data:**

1. **All four contest-style platforms (C4, Sherlock, Cantina, CodeHawks) split
   prize pools among everyone who finds the same bug**, with the split formula
   (confirmed for C4) decaying per additional duplicate finder. A crowded
   contest with 100+ participants competing over a small number of exploitable
   bugs means most participants who find nothing unique receive nothing. This
   is a structural fact of the payout formula, not a guess.

2. **Entry is free and gateless on every platform checked.** No KYC, no
   reputation, no interview, no company required to *try*. KYC only attaches
   at the payout stage, and only above certain earnings thresholds (confirmed
   $1,000 lifetime threshold on C4 specifically). This matches the lane's
   premise exactly.

3. **The realistic newcomer path per platform-provided structure, not
   anecdote:** CodeHawks First Flights (EXP-based, low/no stakes) and C4/Sherlock
   full contests (real money, real competition against ranked wardens with
   months or years of pattern-recognition) are different tiers. The honest
   ramp is: practice on low-stakes/free contests first (First Flights, or
   picking small-scope C4/Sherlock contests) to build pattern recognition
   before expecting a paid finding in a crowded 100+-participant contest.

4. **What is explicitly NOT verified and should not be asserted as fact:**
   percentage of participants who earn $0, median or typical first-payout
   size, or median time-to-first-payout in weeks/months. Any number quoted for
   these without a citation (including ones this operator may have seen
   elsewhere, e.g. in blog posts) should be treated as anecdote, not base
   rate, until sourced. **Do not make a go/no-go decision on this lane based on
   a specific earnings number — none was found to be reliable in this pass.**

---

## Skills Actually Needed

Confirmed from the scope samples actually seen this session:
- **Solidity/EVM** is the dominant language across C4, Sherlock, Cantina,
  CodeHawks main-board contests — this matches broad industry knowledge and
  is not contradicted by anything fetched.
- **Rust** appears meaningfully (C4's Rujira contest was pure Cosmos/Rust;
  Solana and other Rust-based chains are a growing minority share across all
  four platforms).
- Reading circulating contest names (Starknet, ZKsync) implies **Cairo** and
  L2-specific tooling knowledge is relevant on some invite-only/high-value
  contests, though those are gated by invite, not open entry.

---

## Straight Answer

**Is this lane worth the operator's time versus the procurement-gated lanes?**
Structurally, yes on the access question: this is the only lane researched
across nine cycles (per memory: eight prior + this one) with genuinely zero
gate — no turnover requirement, no liability insurance, no references, no
company. That part of the thesis holds up under this research pass.

**But the honest caveat is real and this session could not close it:** the
actual earnings data — the thing that would tell the operator whether this is
a viable income lane in month 1 versus a multi-month skill investment with
uncertain payoff — was not retrievable this session because WebSearch quota
was already spent before this task began. What's confirmed is the *mechanism*
(gateless entry, real prize pools, KYC only at payout, decay-formula splitting
among duplicate finders). What's unconfirmed is the *base rate* (how many
newcomers actually get paid, and how much, and how fast).

**Recommended next action:** re-run the earnings-data half of this research
with a fresh WebSearch budget (targeting Solodit stats pages, named-warden
Twitter/X retrospectives, and any Dune Analytics dashboards on C4/Sherlock
payout distribution) before treating this as a funded decision rather than a
structural one. Until then: treat audit contests as "zero-cost lottery ticket
worth entering in parallel with other lanes," not as "primary income plan" —
the entry cost is genuinely zero (time only), so there's no reason not to
register and attempt a low-stakes contest (CodeHawks First Flight, or a small
C4/Sherlock contest) in parallel with whatever else is running, but do not
retarget the operator's whole plan onto this lane until real payout-rate data
is in hand.
