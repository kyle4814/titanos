# TITANOS // MEMORY IRRELEVANCE PROTOCOL (MAGL_CORE_001)
## Codename: The Forgetting Machine

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Eleventh doctrine file. **Compressed intentionally** — a doctrine whose
whole point is "distill recurring information into smaller structured
representations" does not get preserved as a 500-line prose restatement
of itself; that would be the exact anti-pattern §3 (Distillation Law)
names. Full original text is in this session's transcript (Tier 4 —
provenance archive), not duplicated here.

## THE CORE CLAIM

Historical conversation, exploratory reasoning, and repeated explanation
must not remain permanent runtime dependencies. Knowledge that proves
useful should be compressed into durable, inspectable, executable
artifacts (code/tests/schemas/state) rather than carried forward as
prose. Five tiers, by loading discipline: **Tier 0** invariants (small,
operational, boot-loaded), **Tier 1** live state (boot-loaded), **Tier
2** executable knowledge (code/tests, the preferred durable form),
**Tier 3** indexed doctrine (rationale — retrieved selectively, never
loaded by default), **Tier 4** provenance archive (history — not loaded
by default, exists for recovery/audit). "The system should earn the
right to forget": archive detail once its outcome is preserved, its
rationale is captured, its current state is represented elsewhere, and
its retrieval path is known.

## AUDIT RESULT, SAME DAY — SEE `MEMORY_MAP.md`

Built priority item 1 of this doctrine's own build order (MEMORY MAP)
before any other item, per this repo's own standing Next-Lever
Sequencer rule (a lower-priority item is never legitimate while a
higher one is unresolved). `MEMORY_MAP.md` classifies this repository's
actual content into the five tiers and finds a real, measured problem:
`CLAUDE.md`'s ten `@`-imported doctrine files (now eleven) total 1,700+
lines, all Tier 3 by this doctrine's own definition, but all loaded
unconditionally at every session boot — Tier 3 content paying Tier 0
cost. The cause is a named platform limitation (Claude Code's
`@`-import mechanism has no conditional/lazy-load primitive), not a
design choice this repo made, and is **not solved this cycle** — solving
it (priority item 3, Boot Context Selector) is recorded as
`PARETO_FRONTIER.md` FRONTIER-009, correctly sequenced after this map,
not built prematurely alongside it.

Items 2 (Live State Contract), 4 (Context Dependency Map), 5
(Compaction Record), 6 (Memory Debt Detector) were checked against what
already exists: `NEXT_MOVE.md`/`PARETO_FRONTIER.md`/`HUMAN_DECISIONS.md`
already satisfy item 2 (no gap found); items 4-6 would each be
speculative infrastructure with no current consumer — deferred rather
than built as theater, per this doctrine's own §13 ("create a candidate
only when conversion has clear expected utility").

## THE ONE OPERATIONAL RULE THIS REPO ADOPTS GOING FORWARD

Before adding an 11th, 12th, ... `@`-import to `CLAUDE.md`: ask this
doctrine's own §10 question — "why must this be loaded every time?" —
and answer it in the new file's own opening note, the same way every
doctrine file since `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md` has
already been required to state what it reuses vs. duplicates. This
doctrine file does not add new enforcement code — it adds a checked
discipline for future doctrine growth, which is itself the correct,
minimal Tier-2-eligible artifact this cycle: not code, because the
underlying loading mechanism cannot be gated in code (see the named
platform limitation), so the smallest honest compiled form available is
a documented, repeatable check applied at each future doctrine-file
addition.
