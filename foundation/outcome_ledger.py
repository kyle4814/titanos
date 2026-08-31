"""What we knew before we acted, and what the world did afterwards.

WHY THIS EXISTS, AFTER INSPECTING WHAT DIDN'T

The radar can now discriminate targets. Nothing yet shows that any of its
facts predicts an investigation being worth doing, and it cannot: there is
no surviving link between a decision and its result. Two specific arrows
were missing, both confirmed by reading the live canon rather than assumed:

- `Receipt` carries no reference to the opportunity, map entry or activity
  shape that justified acting. `evidence_refs` is free text and cannot be
  relied on structurally.
- `GoldBrick.human_value_status` exists and defaults to UNKNOWN -- but the
  brick is `frozen=True`, so an outcome can never be attached to it. The
  field is a permanent UNKNOWN by construction.

WHAT THIS REUSES RATHER THAN DUPLICATES

- The append-only, no-delete, `supersedes`-for-correction pattern of
  `CrystalStore` and `RealityYieldLedger`. Same discipline, not a copy of
  their contents.
- `GoldBrick`'s content-addressed identity: an outcome cites a `brick_id`,
  which already commits to its receipt, so nothing here re-derives a
  second chain of custody.

WHY NEITHER EXISTING STORE COULD CARRY IT

`Crystal` records what was believed during a build cycle and what would
disprove it -- no brick, no witness, no outcome ladder. `RealityYieldLedger`
answers "was this worth it" in cost and yield terms, which is a different
question from "what did the world actually do". Extending either would
have meant bending an honest object into a shape it does not mean.

THE RULE THAT MAKES THIS WORTH ANYTHING

The system must never calibrate a decision using facts it learned after
making it. `PreActionContext` is content-addressed and frozen before the
act; an outcome REFERENCES it by id and can never edit it. Any future
analysis that wants to know "what did we know at the time" reads the
snapshot, not a field somebody updated later.

AND THE RULE THAT KEEPS IT HONEST

Silence is not failure. A brick nobody answered is NOT_OBSERVED, which is
a different fact from one a human read and rejected. Collapsing those
would poison the dataset this exists to create.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

# Same shape as foundation/authority_sigil.py::ReleaseLedger and
# kpm/source-vault/registry.py: in-memory dict as the fast path, JSONL as
# the durable replay-on-construction paper trail.
_DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "outcome_ledger.jsonl"

__all__ = [
    "OutcomeIntegrityError",
    "OUTCOME_STATES",
    "EXTERNALLY_EVIDENCED_STATES",
    "TERMINAL_UNOBSERVED",
    "PreActionContext",
    "Witness",
    "OutcomeRecord",
    "OutcomeLedger",
    "LedgerTampered",
    "freeze_pre_action",
    "CHAIN_VERIFIED",
    "CHAIN_UNVERIFIED_LEGACY",
]

# A record's place in the file is itself evidence: deleting or reordering a
# LINE was previously invisible, because each record only content-addressed
# ITSELF (PreActionContext.is_intact()), never its neighbour. Two statuses,
# never conflated: a record chained to its predecessor and verified across
# the whole run of chained lines, versus a record written before this
# feature existed, which the chain literally cannot speak to. The second
# status is not "assumed fine" -- it is a distinct, queryable fact so a
# caller cannot mistake "never checked" for "checked and passed."
CHAIN_VERIFIED = "CHAIN_VERIFIED"
CHAIN_UNVERIFIED_LEGACY = "CHAIN_UNVERIFIED_LEGACY"


class OutcomeIntegrityError(ValueError):
    """An outcome claimed more than the world actually said."""


# The ladder, in the order the existing canon already uses. Each rung is a
# genuinely different fact and none of them implies the next.
OUTCOME_STATES = (
    "PENDING",              # routed, nothing back yet
    "NOT_OBSERVED",         # we looked and the world said nothing
    "DELIVERY_ATTEMPTED",   # we tried to put it through a door
    "ACCEPTED_BY_PLATFORM", # transport succeeded -- a machine, not a person
    "HUMAN_RESPONDED",      # an identifiable person replied
    "VALUE_WITNESSED",      # someone attested it was useful
    "VALUE_REALIZED",       # a real outcome was obtained
    "CASH_REALIZED",        # verified money
    "DECLINED",             # an identifiable human said no
    # A killing experiment positively excluded the target BEFORE any
    # approach was made. Deliberately distinct from both neighbours:
    # NOT_OBSERVED means we looked and the world was silent, DECLINED
    # means a person refused us. This means we investigated and the
    # evidence ruled the target out on its own terms, with no contact
    # ever made. Collapsing it into either one would lose the only
    # outcome the system can reach without spending an approach.
    "DISPROVEN",
    "UNKNOWN",              # not established either way
)

# Above transport, a claim needs a witness. A platform accepting an HTTP
# request is evidence about a server, not about a human finding value.
EXTERNALLY_EVIDENCED_STATES = ("HUMAN_RESPONDED", "VALUE_WITNESSED",
                               "VALUE_REALIZED", "CASH_REALIZED", "DECLINED")

# States that mean "the world has not answered". None of them is a
# negative result, and none may be counted as one.
TERMINAL_UNOBSERVED = ("PENDING", "NOT_OBSERVED", "UNKNOWN")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PreActionContext:
    """Everything the system believed at the moment it decided to act.

    Content-addressed, so a later edit produces a different id and the
    substitution is detectable. This is the answer key's sealed envelope:
    it is written before the world responds and is never rewritten after.
    """

    context_id: str
    target: str
    target_established_by: str
    facts: Mapping[str, Any]
    unknowns: tuple[str, ...] = ()
    disqualifiers: tuple[str, ...] = ()
    frozen_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise OutcomeIntegrityError("a pre-action context must name a target")
        if not self.context_id.startswith("PA-"):
            raise OutcomeIntegrityError(
                "a pre-action context id must be content-derived; use "
                "freeze_pre_action() rather than assigning one")
        object.__setattr__(self, "facts", dict(self.facts))

    def digest(self) -> str:
        return _digest_for(self.target, self.target_established_by,
                           self.facts, self.unknowns, self.disqualifiers)

    def is_intact(self) -> bool:
        """False if any field was altered after freezing."""
        return self.context_id == f"PA-{self.digest()}"


def _digest_for(target: str, established_by: str, facts: Mapping[str, Any],
                unknowns: tuple, disqualifiers: tuple) -> str:
    blob = json.dumps({
        "target": target, "target_established_by": established_by,
        "facts": dict(facts), "unknowns": list(unknowns),
        "disqualifiers": list(disqualifiers),
    }, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _canonical_record_hash(obj: Mapping[str, Any]) -> str:
    """One deterministic digest over a line's own content plus the link to
    its predecessor.

    Canonical form (`sort_keys=True, separators=(",", ":")`) matters: the
    same logical record must hash identically regardless of dict insertion
    order, or two honest writers could disagree about a hash that never
    actually changed. `record_hash` is excluded from its own input --
    hashing a field that contains itself is undefined, not merely awkward.
    `previous_hash` is INCLUDED, which is the whole mechanism: it is what
    turns a bag of self-addressed records into a chain where removing or
    reordering one line breaks the link the next line depends on.
    """
    payload = {k: v for k, v in obj.items() if k != "record_hash"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def freeze_pre_action(target: str, target_established_by: str,
                      facts: Mapping[str, Any],
                      unknowns: tuple[str, ...] = (),
                      disqualifiers: tuple[str, ...] = ()) -> PreActionContext:
    """Seal what is believed now, before acting.

    `facts` is deliberately an open mapping rather than a fixed schema: the
    radar's vocabulary is still moving, and a rigid schema here would
    either block new measurements or invite a second one to be invented.
    What matters is that whatever went in is sealed, not that this module
    dictates the list.
    """
    if not str(target).strip():
        raise OutcomeIntegrityError("a pre-action context must name a target")
    return PreActionContext(
        context_id=f"PA-{_digest_for(target, target_established_by, facts, tuple(unknowns), tuple(disqualifiers))}",
        target=target, target_established_by=target_established_by,
        facts=dict(facts), unknowns=tuple(unknowns),
        disqualifiers=tuple(disqualifiers))


@dataclass(frozen=True)
class Witness:
    """Who observed the outcome, when, and by what mechanism.

    Without this, "VALUE_WITNESSED" is the system grading its own homework.
    `observed_by` must name something outside this system -- a maintainer,
    a platform, a named human -- and `mechanism` must say how, so a later
    reader can go and check.
    """

    observed_by: str
    mechanism: str
    what_was_observed: str
    observed_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        for name in ("observed_by", "mechanism", "what_was_observed"):
            if not str(getattr(self, name)).strip():
                raise OutcomeIntegrityError(
                    f"a witness must state {name}; an outcome nobody can "
                    f"go and check is an opinion with a timestamp")
        if self.observed_by.strip().lower() in _SELF_NAMES:
            raise OutcomeIntegrityError(
                f"{self.observed_by!r} is this system; it cannot witness "
                f"its own value. Name the external party who did.")


_SELF_NAMES = frozenset({
    "titanos", "demonblade", "claude", "the system", "self", "us", "me",
    "the model", "the agent", "internal"})


@dataclass(frozen=True)
class OutcomeRecord:
    """One thing the world did, tied to one brick and one sealed context."""

    outcome_id: str
    brick_id: str
    pre_action_id: str
    state: str
    witness: Optional[Witness] = None
    note: str = ""
    recorded_at: str = field(default_factory=_now)
    supersedes: Optional[str] = None

    def __post_init__(self) -> None:
        if self.state not in OUTCOME_STATES:
            raise OutcomeIntegrityError(f"unknown outcome state {self.state!r}")
        if not self.brick_id.strip():
            raise OutcomeIntegrityError(
                "an outcome must name the artifact it is about; an unattached "
                "outcome cannot calibrate anything")
        if not self.pre_action_id.startswith("PA-"):
            raise OutcomeIntegrityError(
                "an outcome must reference the sealed pre-action context, or "
                "there is nothing to compare the result against")
        if self.state in EXTERNALLY_EVIDENCED_STATES and self.witness is None:
            raise OutcomeIntegrityError(
                f"{self.state} requires a witness. A platform accepting a "
                f"request is evidence about a server, not about a human "
                f"finding value.")

    def is_unobserved(self) -> bool:
        """Distinct from a negative result. Silence is data, not failure."""
        return self.state in TERMINAL_UNOBSERVED

    def is_negative(self) -> bool:
        """Only an identifiable human saying no is a no."""
        return self.state == "DECLINED"

    def counts_as_external_evidence(self) -> bool:
        return self.state in EXTERNALLY_EVIDENCED_STATES


class LedgerTampered(OutcomeIntegrityError):
    """A sealed context on disk no longer matches its own identity."""


class OutcomeLedger:
    """Append-only. Outcomes are corrected by superseding, never by editing.

    Same discipline as `CrystalStore` and `RealityYieldLedger`: there is no
    delete surface and no update surface, because a dataset that can be
    quietly rewritten after the fact cannot calibrate anything.

    DURABILITY, AND WHY IT IS PART OF THE INVARIANT

    Calibration needs outcomes to ACCUMULATE. A dataset held only in
    memory cannot accumulate past a process exit, which makes the stated
    bottleneck -- outcome volume -- unreachable by construction. That was
    a real defect in this module: the first genuine pre-action/outcome
    pair was computed and then lost when its process ended.

    The JSONL path and replay follow `authority_sigil.py::ReleaseLedger`
    exactly, including fail-soft over a truncated trailing line, so a
    crash mid-write can only ever lose the last unflushed append.

    ONE ADDITION THAT LEDGER DOES NOT NEED. Every sealed context is
    re-verified with `is_intact()` on reload. The no-time-travel guarantee
    is worthless if it holds in memory and not across the process
    boundary: someone editing the file could otherwise change what the
    system "believed" before it acted. A tampered context raises rather
    than loading quietly.

    THE GAP THAT WAS FOUND, AND WHY IT WAS INVISIBLE. `is_intact()` proves
    a record was not EDITED -- it says nothing about a record that was
    REMOVED. A middle line deleted (or two lines swapped) from the raw
    JSONL leaves every remaining line individually self-consistent; replay
    would happily rebuild a shorter, or reordered, history and never know.
    Every new record now carries `previous_hash` (the `record_hash` of the
    line written before it, `""` for the first chained record) and its own
    `record_hash` (a digest over its own content INCLUDING `previous_hash`
    -- see `_canonical_record_hash`). Deleting or reordering a chained line
    breaks the link the following line depends on, and replay raises
    `LedgerTampered` naming the line and the break, instead of silently
    reconstructing a shorter past.

    BACKWARD COMPATIBILITY. The file this module has been writing since
    before this feature has no hash fields at all. Those records are not
    an error -- they predate the chain and the chain literally has nothing
    to check them against. They load, and are reported via
    `chain_status()` as `CHAIN_UNVERIFIED_LEGACY`, never as verified. The
    first record appended after a run of legacy lines starts a fresh
    chain from `previous_hash=""` -- it cannot retroactively chain to
    unhashed history, so it does not pretend to.
    """

    def __init__(self,
                 ledger_path: "str | Path | None" = _DEFAULT_LEDGER_PATH) -> None:
        self._ledger_path = Path(ledger_path) if ledger_path else None
        self._records: list[OutcomeRecord] = []
        self._contexts: dict[str, PreActionContext] = {}
        # The hash chain's running state. "" means "nothing chained yet" --
        # true both at the very start of a file AND immediately after a
        # run of legacy (unhashed) lines, which is exactly the behaviour
        # requirement 2 wants: the first chained record's previous_hash is
        # "" whether it opens the file or resumes after legacy history.
        self._chain_next_previous: str = ""
        self._chain_status: dict[str, str] = {}
        if self._ledger_path and self._ledger_path.exists():
            self._replay()

    # -- durability --------------------------------------------------
    def _replay(self) -> None:
        with open(self._ledger_path, "r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    # A truncated trailing write from a killed process looks
                    # exactly like this: a half-written final line that is
                    # not valid JSON. Skipping it (rather than raising) is
                    # deliberate -- a crash may only ever cost the last
                    # unflushed append, never force destructive manual
                    # recovery of everything before it. A deletion/reorder
                    # in the MIDDLE never produces invalid JSON -- the
                    # surviving lines are each still well-formed -- so it is
                    # caught below, by the chain check, not here.
                    continue
                try:
                    self._replay_line(obj, line_no)
                except (KeyError, TypeError):
                    continue

    def _replay_line(self, obj: dict, line_no: int) -> None:
        kind = obj.get("kind")
        if kind == "CONTEXT":
            ctx = PreActionContext(
                context_id=obj["context_id"], target=obj["target"],
                target_established_by=obj["target_established_by"],
                facts=obj.get("facts", {}),
                unknowns=tuple(obj.get("unknowns", ())),
                disqualifiers=tuple(obj.get("disqualifiers", ())),
                frozen_at=obj.get("frozen_at", ""))
            if not ctx.is_intact():
                raise LedgerTampered(
                    f"sealed context {ctx.context_id} on disk does not match "
                    f"its own content; what the system believed before acting "
                    f"has been altered")
            self._verify_chain_link(obj, ctx.context_id, line_no)
            self._contexts[ctx.context_id] = ctx
        elif kind == "OUTCOME":
            w = obj.get("witness")
            record = OutcomeRecord(
                outcome_id=obj["outcome_id"], brick_id=obj["brick_id"],
                pre_action_id=obj["pre_action_id"], state=obj["state"],
                witness=Witness(**w) if w else None,
                note=obj.get("note", ""),
                recorded_at=obj.get("recorded_at", ""),
                supersedes=obj.get("supersedes"))
            self._verify_chain_link(obj, record.outcome_id, line_no)
            self._records.append(record)

    def _verify_chain_link(self, obj: dict, record_id: str,
                           line_no: int) -> None:
        """Advance (or refuse to advance) the running chain state for one
        replayed line. Every branch either records an honest status or
        raises -- there is no third, silent, "probably fine" outcome."""
        record_hash = obj.get("record_hash")
        if record_hash is None:
            # Pre-dates the chain. Not tampering -- there is nothing here
            # to verify against -- but it must never be reported as if it
            # had been.
            self._chain_status[record_id] = CHAIN_UNVERIFIED_LEGACY
            return
        previous_hash = obj.get("previous_hash", "")
        if previous_hash != self._chain_next_previous:
            raise LedgerTampered(
                f"line {line_no}: record {record_id} claims "
                f"previous_hash={previous_hash!r}, but the chain built from "
                f"every line read so far expects {self._chain_next_previous!r}. "
                f"A line was deleted, reordered, or the ledger was cut and "
                f"resumed from a different point -- the two hashes can only "
                f"disagree if the sequence of lines actually on disk differs "
                f"from the sequence this record was written into.")
        recomputed = _canonical_record_hash(obj)
        if recomputed != record_hash:
            raise LedgerTampered(
                f"line {line_no}: record {record_id} does not match its own "
                f"record_hash; its content was altered in place after being "
                f"written (this is the same class of tampering "
                f"PreActionContext.is_intact() already catches for sealed "
                f"contexts, extended here to every chained line).")
        self._chain_status[record_id] = CHAIN_VERIFIED
        self._chain_next_previous = record_hash

    def _append(self, obj: dict) -> None:
        if not self._ledger_path:
            return
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True, default=str) + "\n")

    def _append_chained(self, obj: dict, record_id: str) -> None:
        """Write one line, linking it to whatever was written before it
        (in THIS process's view of the chain -- which, after a
        constructor-time replay, already reflects the whole file)."""
        chained = dict(obj, previous_hash=self._chain_next_previous)
        chained["record_hash"] = _canonical_record_hash(chained)
        self._append(chained)
        self._chain_next_previous = chained["record_hash"]
        self._chain_status[record_id] = CHAIN_VERIFIED

    # -- chain status --------------------------------------------------
    def chain_status(self, record_id: str) -> str:
        """CHAIN_VERIFIED, CHAIN_UNVERIFIED_LEGACY, or "UNKNOWN_RECORD" if
        no context or outcome with this id was ever loaded or written.
        Never returns a verified status for a record this ledger has not
        actually checked -- silence about the chain is not the same fact
        as a passed check, and this method exists so a caller can never
        confuse the two."""
        return self._chain_status.get(record_id, "UNKNOWN_RECORD")

    def seal(self, context: PreActionContext) -> PreActionContext:
        """Store a pre-action snapshot. Re-sealing an identical context is
        idempotent; re-sealing a DIFFERENT one under the same id is
        refused, because that is the substitution this design exists to
        prevent."""
        if not context.is_intact():
            raise OutcomeIntegrityError(
                f"pre-action context {context.context_id} was altered after "
                f"freezing; its content no longer matches its id")
        existing = self._contexts.get(context.context_id)
        if existing is not None and existing.digest() != context.digest():
            raise OutcomeIntegrityError(
                "refusing to replace a sealed pre-action context")
        if context.context_id not in self._contexts:
            self._contexts[context.context_id] = context
            self._append_chained({
                "kind": "CONTEXT", "context_id": context.context_id,
                "target": context.target,
                "target_established_by": context.target_established_by,
                "facts": dict(context.facts),
                "unknowns": list(context.unknowns),
                "disqualifiers": list(context.disqualifiers),
                "frozen_at": context.frozen_at}, context.context_id)
        return context

    def record(self, brick_id: str, context: PreActionContext, state: str,
               witness: Optional[Witness] = None, note: str = "",
               supersedes: Optional[str] = None) -> OutcomeRecord:
        self.seal(context)
        outcome_id = "OC-" + hashlib.sha256(
            f"{brick_id}|{context.context_id}|{state}|{_now()}|"
            f"{len(self._records)}".encode()).hexdigest()[:16]
        record = OutcomeRecord(
            outcome_id=outcome_id, brick_id=brick_id,
            pre_action_id=context.context_id, state=state, witness=witness,
            note=note, supersedes=supersedes)
        self._records.append(record)
        self._append_chained({
            "kind": "OUTCOME", "outcome_id": record.outcome_id,
            "brick_id": record.brick_id, "pre_action_id": record.pre_action_id,
            "state": record.state, "note": record.note,
            "recorded_at": record.recorded_at, "supersedes": record.supersedes,
            "witness": ({"observed_by": record.witness.observed_by,
                         "mechanism": record.witness.mechanism,
                         "what_was_observed": record.witness.what_was_observed,
                         "observed_at": record.witness.observed_at}
                        if record.witness else None)}, record.outcome_id)
        return record

    def context_for(self, outcome: OutcomeRecord) -> Optional[PreActionContext]:
        """What the system knew BEFORE this outcome existed."""
        return self._contexts.get(outcome.pre_action_id)

    def outcomes_for_brick(self, brick_id: str) -> tuple[OutcomeRecord, ...]:
        return tuple(r for r in self._records if r.brick_id == brick_id)

    def current_for_brick(self, brick_id: str) -> Optional[OutcomeRecord]:
        """The latest non-superseded outcome for one artifact."""
        superseded = {r.supersedes for r in self._records if r.supersedes}
        live = [r for r in self.outcomes_for_brick(brick_id)
                if r.outcome_id not in superseded]
        return live[-1] if live else None

    def all_records(self) -> tuple[OutcomeRecord, ...]:
        return tuple(self._records)

    def pairs(self) -> tuple[tuple[PreActionContext, OutcomeRecord], ...]:
        """The dataset calibration will eventually need: what we believed,
        paired with what happened. Never the other way round."""
        out = []
        for r in self._records:
            ctx = self._contexts.get(r.pre_action_id)
            if ctx is not None:
                out.append((ctx, r))
        return tuple(out)
