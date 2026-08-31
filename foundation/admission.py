"""The loading dock: from a bounded mission to a claimed unit of work.

WHAT WAS MISSING, MEASURED NOT ASSUMED

`InvestigationMission` already carries the whole semantic checklist a work
unit needs -- target, why it was selected, what is known, what is unknown,
the cheapest disproof, what would disprove its value, stop conditions,
disqualifiers, power and confidence kept separate. Nothing here rebuilds
any of that.

What did not exist, confirmed by reading the canon:

- No canonical identity for a unit of investigation work, so the same
  question could be picked up twice.
- No claiming, so two investigators could burn time on one target.
- No link from a mission to the receipt or brick it eventually produced --
  grep found zero references in either direction.
- No terminal vocabulary that can say DISPROVEN honestly.

WHY task_queue COULD NOT CARRY IT

`TaskQueue` has a real transition table and this module reuses that
discipline -- an illegal transition is ABSENT from the mapping, not
rejected by a scattered if-check. But `Task` is mutable and its terminal
states are DONE and FAILED, and an investigation that ends DISPROVEN did
not fail. Neither did one that ends WITHHELD because the finding is
security-sensitive. Collapsing those into FAILED would destroy exactly
the honest terminal facts this exists to produce, so the pattern is
reused and the object is not.

THE RULE THAT KEEPS THE FACTORY HONEST

Throughput is a capacity measurement, never a truth signal. This module
counts what it can admit; it never rewards admitting more. There is
deliberately no `bricks_per_day`, no score, and no ranking -- the quality
gate stays upstream in the lock and the opportunity gate, and the outcome
ledger stays downstream. The queue sits between them and rewrites
neither.

A terminal state of DISPROVEN is a productive output. Most missions
should end without a brick.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from foundation.outcome_ledger import PreActionContext, freeze_pre_action

__all__ = [
    "AdmissionRefused",
    "WorkIntegrityError",
    "WORK_STATES",
    "TERMINAL_STATES",
    "TRANSITIONS",
    "REFUSAL_REASONS",
    "can_transition",
    "work_identity",
    "AdmittedWork",
    "AdmissionLedger",
]


class WorkIntegrityError(ValueError):
    """A work unit tried to claim a state it did not earn."""


class AdmissionRefused(Exception):
    """The gate said no. Carries the canonical reason, never a bare no."""

    def __init__(self, reason: str, detail: str) -> None:
        if reason not in REFUSAL_REASONS:
            raise WorkIntegrityError(f"unknown refusal reason {reason!r}")
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


REFUSAL_REASONS = (
    "DUPLICATE",              # this exact question is already admitted
    "ALREADY_CONCLUDED",      # it was investigated and reached a terminal fact
    "DISQUALIFIED",           # a blocking disqualifier is present
    "NO_BOUNDED_QUESTION",    # nothing names what would be investigated
    "NO_STOP_CONDITION",      # work that cannot end is work that eats days
)

# ADMITTED and CLAIMED are the only non-terminal states. Everything else is
# an honest terminal fact, and most of them are not "success".
WORK_STATES = (
    "ADMITTED", "CLAIMED",
    "DISPROVEN",                # the cheapest experiment killed it
    "EVIDENCE_INSUFFICIENT",    # could not be settled within scope
    "AMBIGUOUS",                # settled, but not into one answer
    "WITHHELD",                 # real, and deliberately not routed
    "SECURITY_SENSITIVE",       # never travels the ordinary door
    "HUMAN_REVIEW_REQUIRED",    # a person must decide
    "QUALIFIED",                # earned a receipt
)

TERMINAL_STATES = WORK_STATES[2:]

# Same discipline as task_queue and kpm's promotion state machine: an
# illegal transition is absent from this table, not caught by an if.
TRANSITIONS: dict[str, frozenset[str]] = {
    "ADMITTED": frozenset({"CLAIMED"}),
    "CLAIMED": frozenset(TERMINAL_STATES),
    **{s: frozenset() for s in TERMINAL_STATES},
}


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, frozenset())


def work_identity(target: str, question: str) -> str:
    """One target plus one bounded question is one unit of work.

    Content-derived rather than assigned, so the same question asked twice
    collides by construction instead of relying on a caller to remember.
    Deliberately NOT keyed on the target alone: a repository can honestly
    support several distinct investigations, and collapsing those would
    refuse real work.
    """
    norm = f"{target.strip().lower()}|{' '.join(question.lower().split())}"
    return "WU-" + hashlib.sha256(norm.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class AdmittedWork:
    """A mission that passed the gate, with its state and its links.

    Frozen. State changes produce a new record in the ledger rather than
    editing this one, so the history of a work unit cannot be rewritten
    after the fact -- the same reason the outcome ledger is append-only.
    """

    work_id: str
    target: str
    question: str
    state: str
    pre_action_id: str
    opportunity_id: str = ""
    claimed_by: str = ""
    receipt_id: str = ""
    brick_id: str = ""
    note: str = ""
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.state not in WORK_STATES:
            raise WorkIntegrityError(f"unknown work state {self.state!r}")
        if not self.pre_action_id.startswith("PA-"):
            raise WorkIntegrityError(
                "admitted work must reference a sealed pre-action context, or "
                "the outcome can never be compared against what we believed")
        if self.state == "QUALIFIED" and not self.receipt_id:
            raise WorkIntegrityError(
                "QUALIFIED requires the receipt that qualified it; a work "
                "unit cannot promote itself without the evidence")
        if self.state == "CLAIMED" and not self.claimed_by:
            raise WorkIntegrityError("a claim must name who claimed it")

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def produced_value(self) -> bool:
        """Only QUALIFIED earned anything. DISPROVEN is a productive
        output, but it is not value -- and this is the one place a
        throughput count could quietly start lying."""
        return self.state == "QUALIFIED"


class AdmissionLedger:
    """Append-only. Work units are progressed by appending, never by edit.

    No delete surface, no update surface, and deliberately no method that
    counts admissions as an achievement.
    """

    def __init__(self) -> None:
        self._history: list[AdmittedWork] = []
        self._contexts: dict[str, PreActionContext] = {}

    # -- reads -------------------------------------------------------
    def current(self, work_id: str) -> Optional[AdmittedWork]:
        for record in reversed(self._history):
            if record.work_id == work_id:
                return record
        return None

    def history_for(self, work_id: str) -> tuple[AdmittedWork, ...]:
        return tuple(r for r in self._history if r.work_id == work_id)

    def all_records(self) -> tuple[AdmittedWork, ...]:
        return tuple(self._history)

    def open_work(self) -> tuple[AdmittedWork, ...]:
        """Admitted or claimed, not yet concluded."""
        seen, out = set(), []
        for record in reversed(self._history):
            if record.work_id in seen:
                continue
            seen.add(record.work_id)
            if not record.is_terminal():
                out.append(record)
        return tuple(reversed(out))

    def context_for(self, work_id: str) -> Optional[PreActionContext]:
        record = self.current(work_id)
        return self._contexts.get(record.pre_action_id) if record else None

    # -- writes ------------------------------------------------------
    def admit(self, mission, facts: Optional[dict] = None) -> AdmittedWork:
        """Admit one bounded mission, or refuse with a canonical reason.

        `mission` is an `InvestigationMission` (duck-typed so this module
        does not import the hunter and create a cycle). Everything the gate
        checks, the mission already carries.
        """
        target = getattr(mission, "target", "")
        question = getattr(mission, "next_cheapest_experiment", "")
        disqualifiers = tuple(getattr(mission, "disqualifiers", ()) or ())
        stops = tuple(getattr(mission, "stop_conditions", ()) or ())

        if not str(question).strip():
            raise AdmissionRefused(
                "NO_BOUNDED_QUESTION",
                "the mission names no experiment, so there is nothing to "
                "investigate and no way to know when to stop")
        if not stops:
            raise AdmissionRefused(
                "NO_STOP_CONDITION",
                "work that cannot end is work that eats days; a mission "
                "must say when to walk away")
        if disqualifiers:
            raise AdmissionRefused(
                "DISQUALIFIED",
                f"blocking disqualifiers present: {', '.join(disqualifiers)}")

        work_id = work_identity(target, question)
        existing = self.current(work_id)
        if existing is not None:
            if existing.is_terminal():
                raise AdmissionRefused(
                    "ALREADY_CONCLUDED",
                    f"this question was already investigated and reached "
                    f"{existing.state}; re-asking it needs new evidence, not "
                    f"a second queue entry")
            raise AdmissionRefused(
                "DUPLICATE",
                f"already admitted as {work_id} in state {existing.state}")

        context = freeze_pre_action(
            target=target,
            target_established_by=getattr(mission, "classification", "UNKNOWN"),
            facts=dict(facts or {}),
            unknowns=tuple(getattr(mission, "unknowns", ()) or ()),
            disqualifiers=disqualifiers)
        self._contexts[context.context_id] = context

        record = AdmittedWork(
            work_id=work_id, target=target, question=question,
            state="ADMITTED", pre_action_id=context.context_id,
            opportunity_id=getattr(mission, "opportunity_id", ""))
        self._history.append(record)
        return record

    def _append(self, current: AdmittedWork, state: str, **kw) -> AdmittedWork:
        if not can_transition(current.state, state):
            raise WorkIntegrityError(
                f"illegal transition {current.state} -> {state} for "
                f"{current.work_id}")
        record = AdmittedWork(
            work_id=current.work_id, target=current.target,
            question=current.question, state=state,
            pre_action_id=current.pre_action_id,
            opportunity_id=current.opportunity_id,
            claimed_by=kw.pop("claimed_by", current.claimed_by),
            receipt_id=kw.pop("receipt_id", current.receipt_id),
            brick_id=kw.pop("brick_id", current.brick_id),
            note=kw.pop("note", ""))
        self._history.append(record)
        return record

    def claim(self, work_id: str, by: str) -> AdmittedWork:
        current = self.current(work_id)
        if current is None:
            raise WorkIntegrityError(f"no such work unit {work_id}")
        if not str(by).strip():
            raise WorkIntegrityError("a claim must name who claimed it")
        if current.state == "CLAIMED":
            raise AdmissionRefused(
                "DUPLICATE",
                f"{work_id} is already claimed by {current.claimed_by!r}; two "
                f"investigators on one question is the waste this prevents")
        return self._append(current, "CLAIMED", claimed_by=by)

    def conclude(self, work_id: str, state: str, receipt_id: str = "",
                 note: str = "") -> AdmittedWork:
        """Record the honest terminal fact. Most of these are not value."""
        current = self.current(work_id)
        if current is None:
            raise WorkIntegrityError(f"no such work unit {work_id}")
        if state not in TERMINAL_STATES:
            raise WorkIntegrityError(
                f"{state!r} is not a terminal fact; conclude() ends work")
        return self._append(current, state, receipt_id=receipt_id, note=note)

    def attach_brick(self, work_id: str, brick_id: str) -> AdmittedWork:
        """Link the materialised brick back to the work that earned it.

        Only QUALIFIED work may carry a brick: a brick without a receipt is
        the collapse `gold_brick.py` already refuses, and this is the
        second, independent point that refuses it.
        """
        current = self.current(work_id)
        if current is None:
            raise WorkIntegrityError(f"no such work unit {work_id}")
        if current.state != "QUALIFIED":
            raise WorkIntegrityError(
                f"{work_id} is {current.state}; only QUALIFIED work has a "
                f"brick to attach, and a brick without a receipt is not a "
                f"brick")
        record = AdmittedWork(
            work_id=current.work_id, target=current.target,
            question=current.question, state=current.state,
            pre_action_id=current.pre_action_id,
            opportunity_id=current.opportunity_id,
            claimed_by=current.claimed_by, receipt_id=current.receipt_id,
            brick_id=brick_id, note=current.note)
        self._history.append(record)
        return record

    # -- capacity, never merit ---------------------------------------
    def capacity_report(self) -> dict[str, int]:
        """How much the pipe moved. NOT how well it did.

        Deliberately returns raw counts per state with no total, no rate
        and no ratio, because a single headline number is exactly what a
        factory starts optimising instead of the work.
        """
        seen, counts = set(), {}
        for record in reversed(self._history):
            if record.work_id in seen:
                continue
            seen.add(record.work_id)
            counts[record.state] = counts.get(record.state, 0) + 1
        return counts
