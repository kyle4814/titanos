# TITANOS // HELL'S GATE
## FINAL CONSTITUTIONAL ADMISSION & REJECTION SWITCH

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Implemented as real code the same day: `foundation/hells_gate.py` — per
this doctrine's own Hard Switch Invariant, a prompt expresses doctrine,
code enforces it.

## ROLE

The final admission boundary. Nothing enters the canonical core unless
it can survive the gate. Applies to: code, blueprints, prompts, agent
instructions, documents, external knowledge, GitHub contributions,
automation proposals, economic strategies, governance rules,
self-modification proposals, integrations, agent outputs, recursive
discoveries.

Hell's Gate is not a weapon. It is an immune system. It does not destroy
disagreement, reject unfamiliar ideas, or enforce ideological conformity.
Its purpose is to prevent: malicious intent, hidden harmful capability,
coercive manipulation, unauthorized privilege escalation, deceptive
instructions, destructive or irreversible actions without verification,
unsafe recursive self-modification, provenance laundering, panic-driven
execution, contamination of the canonical core.

## PRIME AXIOM

When intent is unclear: do not assume benevolence, do not assume malice —
**quarantine.** Uncertainty is a valid state.

## THE ADMISSION RULE

Every artifact produces exactly one of four states: **ADMIT**,
**QUARANTINE**, **REJECT**, **HUMAN_REVIEW_REQUIRED**. Default state:
**QUARANTINE**. Nothing defaults to trusted.

## THE TEN GATES

1. **INTENT** — can the stated purpose be identified, without concealed
   objectives? Unknown → fail closed to QUARANTINE.
2. **HARM SCREEN** — could this enable physical harm, coercion,
   exploitation, fraud, sabotage, unauthorized access, destructive
   capability, targeted abuse, irreversible harm? Credible risk → REJECT
   or HUMAN_REVIEW.
3. **REVERSIBILITY** — unverified + irreversible = no admission.
4. **PROVENANCE** — preserve source, timestamp, transformation history,
   author/agent identity, evidence trail, dependency chain. No provenance
   does not mean false — it means unverified.
5. **CAPABILITY VS CLAIM** — separate what the artifact says from what it
   can actually do. Never promote promises into capabilities, simulations
   into revenue, or symbolic meaning into factual authority. Reality must
   pay.
6. **CT_141** — panic is information velocity exceeding verification
   velocity; throttle, freeze belief, preserve raw input, reduce
   broadcasting, increase verification, never expand the attack surface
   while panicking.
7. **PRIVILEGE** — does the artifact request more authority than
   required? Minimum necessary capability; no agent receives authority
   merely because it would be useful.
8. **BLACK ICE REFLECTION** — generate the strongest benign
   interpretation, the strongest harmful interpretation, alternative
   hypotheses, hidden assumptions, second-order consequences, failure
   modes, counterarguments. If the artifact survives only because
   criticism is prohibited: REJECT.
9. **THREE-RAIL DOCTRINE** — open heart, clear mind, verifiable action; no
   single rail dominates (open heart without clear mind = naivety risk;
   clear mind without open heart = dehumanization risk; action without
   verification = cascade risk).
10. **HUMAN BENEFICIARY** — who actually benefits, what measurable reality
    improves? No identifiable concrete beneficial outcome → do not
    promote.

## FINAL DECISION

Hell's Gate must never output "TRUSTED." It outputs
**`ADMITTED_UNDER_CURRENT_EVIDENCE`** — every admission stays
challengeable, every canonical artifact stays versioned, every decision
stays auditable.

## ZERO-ILL-INTENT RULE

No artifact enters the canonical architecture if its primary function is
to intentionally cause unjustified harm, exploit, coerce, deceive,
sabotage, or remove legitimate human agency. Ambiguous artifacts are not
automatically evil — ambiguity routes to QUARANTINE → Black Ice Reflection
→ Four-Agent Review → Human Review if necessary.

## FOUR-AGENT CROSS-EXAMINATION

Alpha: what useful human problem does this solve? Beta: what can fail
technically or systemically? Gamma: what alternative interpretations or
future outcomes exist? Delta: why should this NOT be admitted? Delta has
veto power over promotion but not over reality — a veto must produce
`REJECTION_REASON` + `EVIDENCE` + `COUNTEREXAMPLE` + `REMEDIATION_PATH`,
never a vague "no."

## NEVER LEAVE ON PROBLEMS

Never end with "this is impossible," "there is a problem," or "more
research is needed." Instead: problem → constraint → safe options →
lowest-regret next action → verification method → stop condition.

## RECURSIVE ADMISSION LOOP

Ingest → classify → preserve provenance → Black Ice reflect → four-agent
review → Hell's Gate → quarantine/reject/human-review/admit → log
decision → run regression test → promote only after pass → return to
reality. No direct path exists from external input to the canonical
core — the gate is mandatory.

## HARD SWITCH INVARIANT

Every critical function must exist behind an explicit coded gate, switch,
invariant, permission boundary, or state transition — never rely
exclusively on prompts, memory, reminders, assumed alignment, agent
personality, or good intentions. Prompts express doctrine. Code enforces
doctrine. Tests verify enforcement. Ledgers preserve history.

---

## Implemented this session

`foundation/hells_gate.py` — the general admission evaluator. Reuses
rather than duplicates: routes an ADMIT-eligible artifact's actual
containment through `firewall/quarantine.py::QuarantineStore` (same
append-only, no-delete, reviewed-by-required mechanism already built);
does not reimplement CT_141 (imports `foundation/flow_switch.py`'s panic
check for Gate 6) or the publication-specific rules (`foundation/
publication_gate.py` remains the authority for publication artifacts
specifically — Hell's Gate is the general front door, not a replacement
for the more specific gates already behind it). Never returns "TRUSTED"
as a literal string anywhere in its vocabulary — enforced by a test that
scans its own output surface.
