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
from typing import Any, Mapping, Optional

__all__ = [
    "OutcomeIntegrityError",
    "OUTCOME_STATES",
    "EXTERNALLY_EVIDENCED_STATES",
    "TERMINAL_UNOBSERVED",
    "PreActionContext",
    "Witness",
    "OutcomeRecord",
    "OutcomeLedger",
    "freeze_pre_action",
]


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


class OutcomeLedger:
    """Append-only. Outcomes are corrected by superseding, never by editing.

    Same discipline as `CrystalStore` and `RealityYieldLedger`: there is no
    delete surface and no update surface, because a dataset that can be
    quietly rewritten after the fact cannot calibrate anything.
    """

    def __init__(self) -> None:
        self._records: list[OutcomeRecord] = []
        self._contexts: dict[str, PreActionContext] = {}

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
        self._contexts.setdefault(context.context_id, context)
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
