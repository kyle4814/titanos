"""The adapter between discovered signals and the durable outcome ledger.

WHY THIS EXISTS

`tender_radar.sweep()` produces real `CanonicalSignal` objects -- this
repository's first genuine external ping (six live UK public-sector
tender notices, 2026-09-01) -- and then they evaporate. `sweep()` is
report-only by design (see its own docstring: "no ledger write, no
promotion, no contact"), which is correct for a mouth but leaves nothing
durable behind. `COMMERCIAL_OUTCOME` reads "signals 0 * qualified 0 *
contracts 0 * CASH 0" not because nothing was ever observed, but because
nothing observed was ever recorded anywhere that survives a process exit.

This module is that missing adapter, nothing more. It does not fetch, it
does not score, it does not decide, it does not invent a second ledger or
a second signal type.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation.signal_spine.CanonicalSignal` -- the only signal shape.
  This module takes signals as a plain argument (never imports a specific
  radar), so it works identically for `tender_radar`, any future
  `tender_radar_au`, or any other mouth that ever emits `CanonicalSignal`.
- `foundation.opportunity.controlling_party()` -- the exact function
  `power_profile()` already uses to stop one self-dealing party from
  earning `SOURCE_DIVERSITY` by talking to itself through several API
  doors. Applied here one level up: three tender notices from one buyer
  are not three opportunities, they are one buyer observed three times.
  A genuinely independent second party (a different buyer, or -- per
  that function's own documented nuance -- a different `author_login`
  named inside one signal's evidence) is never merged with the first.
- `foundation.opportunity.opportunity_id_for()` -- the existing stable,
  content-derived identity function, reused so a collapsed opportunity's
  id is deterministic across runs rather than this module inventing a
  second id scheme.
- `foundation.outcome_ledger.OutcomeLedger` -- the one durable
  calibration spine. `freeze_pre_action()` seals what was observed;
  `OutcomeLedger.record(..., operation_id=...)` is the ledger's own
  documented replay-safety mechanism (see that module's `record()`
  docstring) -- this module supplies a deterministic `operation_id` per
  collapsed opportunity+signal-set rather than building a second
  dedup index.

THE HARD RULE THIS MODULE EXISTS TO ENFORCE

A discovered tender notice is OBSERVED demand. It is not a lead, not a
qualified opportunity, not a contract, and not cash.
`MODELLED != OBSERVED != VERIFIED != REALIZED` -- the same discipline
`value_model.py` and `outcome_ledger.py` already enforce, applied here to
the pipeline's own output. `PipelineReport.qualified`, `.contracts` and
`.cash` are hardcoded to `0` and there is no code path in this module
that can ever set them otherwise, because no evidence for any of those
three facts exists anywhere in a `CanonicalSignal`. Making
`COMMERCIAL_OUTCOME` measurable does not mean making it look better than
reality -- "signals: N (real), qualified 0, contracts 0, cash 0" is the
honest, successful outcome this module produces.

A future adapter that DOES have evidence a lead was qualified, a
contract was signed, or cash was verified received must call
`OutcomeLedger.record()` directly with the appropriate state (and, for
anything past `PENDING`, a real external `Witness` -- the ledger itself
refuses `HUMAN_RESPONDED`/`VALUE_WITNESSED`/`VALUE_REALIZED`/
`CASH_REALIZED`/`DECLINED` without one). This module is not that
adapter and does not pretend to be.

WHY `PENDING`, NOT A NEW STATE

`OUTCOME_STATES` has no literal "OBSERVED" rung -- and this module does
not add one, per the standing rule against building a second vocabulary
next to an existing one. Of the states that already exist, `PENDING`
("routed, nothing back yet") is the only honest fit: this pipeline has
routed an externally observed fact into the ledger, and nothing further
(a response, a witness, a qualification) has happened. `NOT_OBSERVED`
would be dishonest in the other direction -- it means we looked and the
world was silent, the opposite of what a real tender notice is.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

from foundation.opportunity import controlling_party, opportunity_id_for
from foundation.outcome_ledger import OutcomeLedger, freeze_pre_action
from foundation.signal_spine import CanonicalSignal

__all__ = [
    "PipelineOpportunity",
    "PipelineReport",
    "collapse_by_controlling_party",
    "run_pipeline",
]

# A fixed handle, not derived from any particular radar, so the same
# controlling party collapses to the same opportunity id regardless of
# which mouth (UK tender radar, a future AU source, anything else) the
# signal originally came from.
_PIPELINE_HANDLE = "opportunity_pipeline"


@dataclass(frozen=True)
class PipelineOpportunity:
    """Every signal this sweep traced to one controlling party, collapsed
    into one identity. Never a claim about qualification, value, or
    contract state -- see module docstring."""

    opportunity_id: str
    controlling_party: str
    signals: tuple[CanonicalSignal, ...]

    def operation_id(self) -> str:
        """Deterministic across re-runs of an identical signal set, and
        different whenever the set of signals for this party genuinely
        changes. This is what makes `OutcomeLedger.record()`'s replay
        safety actually engage: re-running the same sweep produces the
        same operation id and the ledger returns the original record
        instead of appending a second one; a sweep that finds a new
        notice for the same buyer is a new observation and gets a new
        operation id, exactly matching the ledger's own documented
        distinction between a retried write and a genuinely new fact."""
        signal_ids = ",".join(sorted(s.signal_id for s in self.signals))
        raw = f"{self.opportunity_id}|{signal_ids}"
        return "OP-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class PipelineReport:
    """The honest scoreboard. `qualified`, `contracts` and `cash` are
    always `0` -- see module docstring for why that is success, not a
    bug."""

    signal_count: int
    controlling_party_count: int
    opportunities: tuple[PipelineOpportunity, ...]
    qualified: int
    contracts: int
    cash: int

    def show_the_math(self) -> str:
        lines = [
            f"OPPORTUNITY PIPELINE signals={self.signal_count} "
            f"distinct_controlling_parties={self.controlling_party_count} "
            f"qualified={self.qualified} contracts={self.contracts} "
            f"cash={self.cash}",
        ]
        if not self.opportunities:
            lines.append(
                "  zero signals this cycle -- a valid, honest outcome, not "
                "an error")
        for opp in self.opportunities:
            lines.append(
                f"  OBSERVED party={opp.controlling_party!r} "
                f"signals={len(opp.signals)} "
                f"opportunity_id={opp.opportunity_id}")
        if self.opportunities:
            lines.append(
                "  every party above is OBSERVED only: a discovered signal "
                "is demand, not a lead, not a qualified opportunity, not a "
                "contract, and not cash")
        return "\n".join(lines)


def collapse_by_controlling_party(
    signals: Iterable[CanonicalSignal],
) -> tuple[PipelineOpportunity, ...]:
    """Group signals by controlling party, not by target string and not
    by which feed carried them.

    Reuses `opportunity.controlling_party()` exactly as `power_profile()`
    does. The party for each signal is derived from THAT SIGNAL's OWN
    `target` field (never a shared opportunity target passed in from
    outside), because a single sweep may span many different targets --
    many different tender buyers in one feed poll. A signal whose
    evidence names a distinct `author_login` (a genuine third-party
    demand signal on someone else's repository, for instance) is
    correctly treated as its own party rather than folded into the
    target owner -- the exact nuance `controlling_party()`'s own
    docstring calls out as the thing that must survive.
    """
    groups: dict[str, list[CanonicalSignal]] = {}
    order: list[str] = []
    for signal in signals:
        party = controlling_party(signal.target, signal)
        if party not in groups:
            groups[party] = []
            order.append(party)
        groups[party].append(signal)

    opportunities = []
    for party in order:
        group = tuple(groups[party])
        opp_id = opportunity_id_for(party, _PIPELINE_HANDLE)
        opportunities.append(PipelineOpportunity(
            opportunity_id=opp_id, controlling_party=party, signals=group))
    return tuple(opportunities)


def _record_opportunity(ledger: OutcomeLedger, opp: PipelineOpportunity,
                         now: Optional[datetime] = None) -> None:
    signal_ids = tuple(sorted(s.signal_id for s in opp.signals))
    kinds = tuple(sorted({s.kind for s in opp.signals}))
    source_refs = tuple(sorted({s.source_ref for s in opp.signals}))
    context = freeze_pre_action(
        target=opp.controlling_party,
        # Not one of `signal_spine.TARGET_PROVENANCE` on purpose --
        # `PreActionContext` does not restrict this field to that
        # vocabulary (only `CanonicalSignal`/`OpportunityReceipt` do),
        # and inventing a fourth TARGET_PROVENANCE value here to satisfy
        # a check that does not apply would be exactly the kind of
        # unforced second vocabulary this module exists to avoid.
        target_established_by="OBSERVED_SIGNAL_COLLAPSE",
        facts={
            "signal_count": len(opp.signals),
            "signal_ids": signal_ids,
            "signal_kinds": kinds,
            "source_refs": source_refs,
        },
        unknowns=(
            "whether this demand is already being pursued by someone else",
            "whether this party is eligible to respond to us",
            "whether responding would be worthwhile",
        ),
    )
    ledger.record(
        brick_id=opp.opportunity_id,
        context=context,
        state="PENDING",
        note=(
            f"OBSERVED: {len(opp.signals)} signal(s) traced to controlling "
            f"party {opp.controlling_party!r}. This is demand observed, "
            f"not a qualified opportunity, not a contract, not cash."
        ),
        operation_id=opp.operation_id(),
    )


def run_pipeline(
    signals: Iterable[CanonicalSignal],
    ledger: OutcomeLedger,
    now: Optional[datetime] = None,
) -> PipelineReport:
    """Take signals from any radar, collapse by controlling party, record
    each collapsed opportunity into the outcome ledger idempotently, and
    return the honest count.

    `now` is accepted for test determinism symmetry with the rest of
    this repository's sweep functions but is not currently consulted --
    `OutcomeLedger.record()` stamps its own wall-clock time, and this
    module does not second-guess that.
    """
    signals = tuple(signals)
    opportunities = collapse_by_controlling_party(signals)
    for opp in opportunities:
        _record_opportunity(ledger, opp, now=now)
    return PipelineReport(
        signal_count=len(signals),
        controlling_party_count=len(opportunities),
        opportunities=opportunities,
        qualified=0,
        contracts=0,
        cash=0,
    )
