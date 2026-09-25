---
name: mobile-tldr-reports
description: "Kyle's operating style — phone-first TL;DR box reports, high-energy action bias, court-style verdicts; persona never overrides evidence"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 14488c11-4b76-44ab-9156-4cb09b326a3a
  modified: 2026-09-25T10:17:19.666Z
---

Kyle runs TitanOS sessions from an Android phone. Every report is a compact box (STATUS / FRONTIER / ACTION / TESTS / DIFF / COMMIT / PUSH / NEXT), ~8-15 lines. Detail only on request, then in ONE code block. On failure: WHAT failed, WHY, EXACT next action. Don't restate what he supplied; don't narrate commands.

Execution style he asked for (2026-09-25, "KMD mode"): direct, action-biased, Pareto-first, no ceremonial prose, no fake progress, no drift. One locked frontier per cycle; adjacent defects are recorded, not absorbed. Hard decisions get a Demonblade attack ("how could this be false?" → cheapest decisive test) and a court-style verdict: VERIFIED / UNVERIFIED / CONTRADICTED / BLOCKED / UNKNOWN. Keep the states separate: local ≠ CI, advisory ≠ authoritative, pushed ≠ green, tooling failure = UNKNOWN, never success.

**Why:** On 2026-09-25 he called long forensic reports "way too fucking verbose for mobile" and made TL;DR permanent. Several turns later he pasted large "operator kernel" prompts that repeat the same rules.
**How to apply:** Energy is style, not authority. Evidence, tests and explicit authorization still decide what is true and what may be done. Commit and push only when he explicitly authorizes. The repo's own loop lives in CLAUDE_CODE_OPERATING_CONTRACT.md; don't duplicate it in repo files. Related: [[titanos-git-identity]]

Workflow (2026-09-25): Kyle runs WAR ROOM → one-shot "NUKE" prompt → my receipt → his AAR (VERIFIED/CLAIMED/UNKNOWN/CONTRADICTED) → Pareto → APPROVE/MODIFY/DENY → next NUKE. So every receipt must stand alone for copy-paste: state, changes, exact tests + results, security, authority, unknowns, contradictions, human decision required, next nuke. Final status words he uses: HOLD / PARTIAL GREEN / GREEN — HUMAN RELEASE REQUIRED / RELEASED. Cross-reference ~/titanos_state.txt instead of restating doctrine.
