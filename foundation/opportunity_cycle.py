"""The production caller for every registered tender source and
`opportunity_pipeline`.

WHY THIS EXISTS

The prior cycle wired exactly one mouth (`tender_radar.sweep()`, UK
Contracts Finder, 6 live notices) into `opportunity_pipeline.run_pipeline()`
and called it done. Meanwhile `foundation/tender_sources.py` grew a second
registered source (`tender_radar_eu_ted`, EU TED, 7,140 live open notices
matching the operator's CPV filter at last count) with its own mouth
(`foundation/mouth_ted.py`) and its own signal builder (`ted_signal()`,
deliberately separate from `tender_radar.tender_signal()` because that
function hardcodes "UK" into every claim it builds -- see `mouth_ted.py`'s
own docstring). `run_cycle()` never called it. The pipeline was seeing 6
of roughly 7,146 reachable opportunities and reporting that as if it were
the whole world, silently.

THIS CYCLE'S FIX

`run_cycle()` now sweeps every source this module knows how to sweep,
merges their signals into ONE list, and runs that merged list through
`opportunity_pipeline.run_pipeline()` exactly once -- so
`collapse_by_controlling_party()` collapses a buyer appearing in both
feeds into one opportunity, not two. One source failing (network,
malformed feed, exhausted budget) does not abort the others, and the
report never silently looks like a clean 6-signal cycle when a second
source actually returned nothing because it errored -- see
`SourceCycleResult` below, which is the whole point of this fix: a
partial result must be visibly partial.

WHY THIS MODULE, NOT `tender_sources.py`, OWNS THE SOURCE-TO-SWEEPER
MAPPING

`tender_sources.SOURCES` is a registry of *parsers* (bytes -> item-dicts)
plus metadata -- it does not know how to build a `CanonicalSignal` from
those items, because that step is deliberately source-specific (UK's
`tender_signal()` vs TED's `ted_signal()`, see `mouth_ted.py`'s own
docstring for why those cannot be the same function). Each registered
source's full observe -> signal -> report chain already exists as that
source's own `sweep()` function (`tender_radar.sweep()`,
`mouth_ted.sweep()`) -- both return a dataclass with the identical shape
this module actually needs (`status`, `fetched_count`, `error`,
`signals`, `targets`). `_SOURCE_SWEEPERS` below is therefore a small,
honest, hand-maintained map from `tender_sources.list_sources()`'s own
source ids to those existing `sweep()` callables -- reusing both
end-to-end pipelines unchanged, not rebuilding a third. A source
present in the registry but absent from this map (nothing today; a
future source added to `tender_sources.py` without updating this map)
produces an isolated `UNSUPPORTED_SOURCE` result for that one source
rather than crashing the cycle or silently skipping it -- see
`_sweep_one_source()`.

WHAT IT DOES NOT DO, ON PURPOSE

- Does not schedule itself. Same reasoning as before: a scheduled
  entrypoint is a human decision recorded in `HUMAN_DECISIONS.md`.
- Does not touch `autonomy_metric.py`.
- Does not fetch live by default for any source. `fetch_fn` (applied to
  every source that has no more specific override) and `fetch_fns`
  (per-source overrides, keyed by source id) are both injectable, never
  auto-defaulted to a live fetch inside a test. When neither is given
  for a source, that source's own `sweep()` reaches its own default
  fetcher, which goes through `mouth_common.fetch_feed()` and therefore
  through `discovery_authorization.authorize_discovery()` -- no second,
  ungated path exists here, for any source.
- Does not pool or share budget across sources. Each source's `sweep()`
  call reaches that source's own, independently declared
  `DiscoveryPolicy` (`tender_radar.DISCOVERY_POLICY`,
  `mouth_ted.DISCOVERY_POLICY`) exactly as it already did before this
  module existed -- this module introduces no shared budget object.
- Does not write anything by default except through the `OutcomeLedger`
  the caller supplies, and only once, after all sources have been swept
  and merged -- never one ledger write per source.
- Cannot ever set `qualified`, `contracts`, or `cash` above zero, for
  the same reason as before: `opportunity_pipeline.PipelineReport`
  hardcodes all three to `0` and this module only reads them through.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation.tender_sources.list_sources()` -- the registry's own
  source-id enumeration, so a future registered source is picked up by
  iteration rather than a second hardcoded list. (Sweeping it still
  requires adding its `sweep()` function to `_SOURCE_SWEEPERS` below --
  see the note above for why that one line of wiring cannot be avoided.)
- `foundation.tender_radar.sweep()` / `foundation.mouth_ted.sweep()` --
  each source's own complete, already-tested observe -> signal -> report
  chain, called unchanged.
- `foundation.opportunity_pipeline.run_pipeline()` -- the one
  signal -> ledger adapter, called exactly once per cycle on the merged
  signal set, so collapse-by-controlling-party works across sources.
- `foundation.outcome_ledger.OutcomeLedger` -- passed in by the caller,
  never constructed here.

COLD START

Every source's own `sweep()` creates its own state directory
(`state_dir.mkdir(parents=True, exist_ok=True)`) before touching its own
state file inside it (keyed by that source's own `MOUTH_ID`). Passing
the same `state_dir` to every source is therefore safe -- no two
sources' state files collide, and a state directory that has never
existed on this machine is created the first time any source's `sweep()`
runs.

BACKWARDS COMPATIBILITY

`foundation/swarm_contract.py` imports `OpportunityCycleReport` and
calls `run_cycle(state_dir, ledger, fetch_fn=..., now=...)` -- the exact
old call shape. That shape still works unchanged: `fetch_fn`, when given
without `fetch_fns`, is applied as the fetcher for every source that has
no more specific `fetch_fns` override, so a single-source-shaped test
double (e.g. one that returns a UK OCDS `{"releases": [...]}` payload)
still drives the UK source correctly, and drives any other source into
an isolated, reported `UNAVAILABLE` for that source (its parser rejects
the wrong shape) rather than crashing or silently reaching the real
network. `report.sweep_status`, `.sweep_error`, `.signal_count`,
`.controlling_party_count`, `.ledger_records_written`, `.qualified`,
`.contracts`, `.cash` -- every field `swarm_contract.py` reads off the
report -- are all still present, now computed across every source
rather than one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Optional

from foundation.communication_gate import CommunicationDenied
from foundation.discovery_authorization import UnboundedDiscoveryObjective
from foundation.mouth_ted import MOUTH_ID as _TED_MOUTH_ID, sweep as _ted_sweep
from foundation.opportunity_pipeline import PipelineReport, run_pipeline
from foundation.outcome_ledger import OutcomeLedger
from foundation.signal_spine import CanonicalSignal
from foundation.tender_radar import MOUTH_ID as _UK_MOUTH_ID, sweep as _uk_sweep
from foundation.tender_sources import list_sources

# Gate-level refusals, not per-source fetch/parse failures. These come
# from `discovery_authorization.authorize_discovery()` (reached through
# `mouth_common.fetch_feed()` on the real path, or raised directly by an
# injected test `fetch_fn` simulating that path) and represent a policy
# decision about THIS repository's communication authorization, not a
# fact about one source's feed being down. `foundation/swarm_contract.py`
# -- an existing caller this module must not break -- already catches
# these around its own `run_cycle()` call and returns a distinct
# `BUDGET_EXHAUSTED`/`AUTHORITY_HOLD` status; per-source-swallowing them
# here would silently downgrade a budget/authorization refusal into an
# ordinary "one source had a bad day" report, which is the wrong
# severity for a gate decision. They are deliberately NOT caught by
# `_sweep_one_source()` and propagate out of `run_cycle()` unchanged,
# same as before this module swept more than one source.
_GATE_REFUSAL_EXCEPTIONS = (CommunicationDenied, UnboundedDiscoveryObjective)

__all__ = ["SourceCycleResult", "OpportunityCycleReport", "run_cycle"]

# Every registered source this module knows how to sweep, mapped to that
# source's own, already-tested `sweep()` function -- see module
# docstring for why this hand-maintained map is the correct amount of
# wiring rather than something `tender_sources.py` itself should own.
# Every callable here has the identical shape:
#   sweep(state_dir, fetch_fn=None, now=None) -> object with
#       .status: str, .fetched_count: int, .error: Optional[str],
#       .signals: tuple[CanonicalSignal, ...], .targets: tuple[str, ...]
_SOURCE_SWEEPERS: "dict[str, Callable]" = {
    _UK_MOUTH_ID: _uk_sweep,
    _TED_MOUTH_ID: _ted_sweep,
}

# A source status meaning "this cycle does not yet know how to sweep
# this registered source" -- distinct from `mouth_common.MOUTH_STATUSES`
# (which are all about a fetch that was actually attempted) because no
# fetch is attempted at all in this case. Never silently skipped: still
# produces a `SourceCycleResult` so a caller inspecting per-source status
# sees the gap rather than a source that quietly vanished.
_UNSUPPORTED_SOURCE_STATUS = "UNSUPPORTED_SOURCE"

# A sweep status meaning the fetch itself failed for that source
# (mirrors `mouth_common.py`'s own `UNAVAILABLE`) -- both this and
# `_UNSUPPORTED_SOURCE_STATUS` count as "this source contributed zero
# signals and that is visible in the report", the property this whole
# module exists to guarantee.
_FAILURE_STATUSES = ("UNAVAILABLE", _UNSUPPORTED_SOURCE_STATUS)


@dataclass(frozen=True)
class SourceCycleResult:
    """One registered source's own contribution to this cycle, reported
    in isolation -- the record that makes a partial cycle visibly
    partial rather than indistinguishable from a clean one. `error` is
    `None` exactly when `status` is not in `_FAILURE_STATUSES`."""

    source_id: str
    status: str
    error: Optional[str]
    fetched_count: int
    signal_count: int

    def show_the_math(self) -> str:
        line = (
            f"  SOURCE {self.source_id} status={self.status} "
            f"fetched={self.fetched_count} signals={self.signal_count}"
        )
        if self.error:
            line += f"\n    error: {self.error}"
        return line


@dataclass(frozen=True)
class OpportunityCycleReport:
    """One composed cycle's outcome across every registered source: what
    each source saw (`source_results`), what the merged, collapsed set
    looked like, what the pipeline recorded, and the honest zeros. Never
    a claim about qualification, value, or contract state -- see module
    docstring."""

    sweep_status: str
    sweep_error: Optional[str]
    signal_count: int
    controlling_party_count: int
    controlling_parties: tuple = ()
    ledger_records_written: int = 0
    qualified: int = 0
    contracts: int = 0
    cash: int = 0
    source_results: tuple = ()

    def show_the_math(self) -> str:
        lines = [
            f"OPPORTUNITY CYCLE sweep_status={self.sweep_status} "
            f"signals={self.signal_count} "
            f"controlling_parties={self.controlling_party_count} "
            f"ledger_records={self.ledger_records_written} "
            f"qualified={self.qualified} contracts={self.contracts} "
            f"cash={self.cash}",
        ]
        for source_result in self.source_results:
            lines.append(source_result.show_the_math())
        if self.sweep_error:
            lines.append(f"  cycle-level error summary: {self.sweep_error}")
        if self.controlling_parties:
            lines.append(
                "  controlling parties: " + ", ".join(self.controlling_parties))
        if self.signal_count == 0:
            lines.append(
                "  zero signals this cycle -- a valid, honest outcome, not "
                "an error")
        else:
            lines.append(
                "  every party above is OBSERVED only: a discovered signal "
                "is demand, not a lead, not a qualified opportunity, not a "
                "contract, and not cash")
        return "\n".join(lines)


def _sweep_one_source(
    source_id: str,
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]],
    now: Optional[datetime],
) -> "tuple[SourceCycleResult, tuple[CanonicalSignal, ...]]":
    """Sweep exactly one registered source, in isolation. Never raises:
    a source this module has no sweeper for produces an
    `UNSUPPORTED_SOURCE` result; a sweep that itself fails (network,
    malformed feed, exhausted budget) is caught here so it cannot abort
    any other source's sweep, and is reported with its real error text
    rather than swallowed."""
    sweeper = _SOURCE_SWEEPERS.get(source_id)
    if sweeper is None:
        return (
            SourceCycleResult(
                source_id=source_id,
                status=_UNSUPPORTED_SOURCE_STATUS,
                error=(
                    f"{source_id!r} is registered in tender_sources.py "
                    f"but opportunity_cycle.py has no sweeper wired for "
                    f"it yet -- see this module's docstring"
                ),
                fetched_count=0,
                signal_count=0,
            ),
            (),
        )

    try:
        source_sweep = sweeper(state_dir, fetch_fn=fetch_fn, now=now)
    except _GATE_REFUSAL_EXCEPTIONS:
        # A communication/discovery-authorization refusal, not a
        # per-source fetch failure -- let it propagate. See
        # `_GATE_REFUSAL_EXCEPTIONS`'s own comment above for why this is
        # not swallowed here.
        raise
    except Exception as exc:  # noqa: BLE001 -- per-source isolation is the point
        # A source's own `sweep()` is documented never to raise for an
        # ordinary fetch/parse failure (it converts that into a
        # structured `UNAVAILABLE` status internally) -- this except is
        # a second, independent backstop so that even a defect in one
        # source's sweeper cannot take another source down with it,
        # matching this module's own "one source failing must not abort
        # the others" requirement for genuine per-source failures.
        return (
            SourceCycleResult(
                source_id=source_id,
                status="UNAVAILABLE",
                error=f"{type(exc).__name__}: {exc}",
                fetched_count=0,
                signal_count=0,
            ),
            (),
        )

    result = SourceCycleResult(
        source_id=source_id,
        status=source_sweep.status,
        error=source_sweep.error,
        fetched_count=source_sweep.fetched_count,
        signal_count=len(source_sweep.signals),
    )
    return result, tuple(source_sweep.signals)


def _summarize(source_results: "tuple[SourceCycleResult, ...]") -> "tuple[str, Optional[str]]":
    """Roll every source's own status into one honest cycle-level
    summary. `OK` only when every source succeeded; `PARTIAL` when at
    least one succeeded and at least one failed (the case this whole
    module exists to make visible); `ALL_SOURCES_FAILED` when every
    source failed; `NO_SOURCES` if the registry is empty (never true
    today, checked rather than assumed)."""
    if not source_results:
        return "NO_SOURCES", "no sources are registered in tender_sources.py"

    failed = tuple(r for r in source_results if r.status in _FAILURE_STATUSES)
    ok = tuple(r for r in source_results if r.status not in _FAILURE_STATUSES)

    if not failed:
        return "OK", None
    error_summary = "; ".join(f"{r.source_id}: {r.error}" for r in failed)
    if not ok:
        return "ALL_SOURCES_FAILED", error_summary
    return "PARTIAL", error_summary


def run_cycle(
    state_dir: Path,
    ledger: OutcomeLedger,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
    fetch_fns: Optional[Mapping[str, Callable[[], bytes]]] = None,
) -> OpportunityCycleReport:
    """Sweep every registered tender source (`tender_sources.list_sources()`),
    merge their signals, and feed the merged set into
    `opportunity_pipeline.run_pipeline()` exactly once -- so
    collapse-by-controlling-party works ACROSS sources, not per source.

    `state_dir` is handed straight to every source's own `sweep()`,
    which creates it if it does not exist (cold-start safe; safe to
    share across sources -- see module docstring). `ledger` is the
    caller's own `OutcomeLedger` -- this function writes nothing durable
    except through it, once, after the merge.

    `fetch_fn`, when given, is the fetcher used for any source that has
    no more specific override in `fetch_fns` -- this is what keeps
    `swarm_contract.py`'s existing single-`fetch_fn` call shape working
    unchanged (see module docstring's Backwards Compatibility section).
    `fetch_fns` is an optional `{source_id: fetch_fn}` mapping for tests
    that want to inject a different, source-shaped payload per source.
    When a source has neither, its own `sweep()` reaches its own real,
    gated default fetcher.

    One source failing (network, malformed feed, exhausted budget, or a
    registered source this module has no sweeper for) never aborts the
    others -- see `_sweep_one_source()`. The returned report's
    `source_results` names every source's own status/error/counts
    individually, and `sweep_status`/`sweep_error` roll those into one
    honest cycle-level summary (`OK` / `PARTIAL` / `ALL_SOURCES_FAILED` /
    `NO_SOURCES`) that can never look identical between "everything
    worked" and "one source silently contributed nothing".
    """
    fetch_fns = fetch_fns or {}

    source_results = []
    merged_signals: "list[CanonicalSignal]" = []
    for source_id in list_sources():
        source_fetch_fn = fetch_fns.get(source_id, fetch_fn)
        result, signals = _sweep_one_source(source_id, state_dir, source_fetch_fn, now)
        source_results.append(result)
        merged_signals.extend(signals)

    sweep_status, sweep_error = _summarize(tuple(source_results))

    pipeline_report: PipelineReport = run_pipeline(
        tuple(merged_signals), ledger, now=now)

    return OpportunityCycleReport(
        sweep_status=sweep_status,
        sweep_error=sweep_error,
        signal_count=pipeline_report.signal_count,
        controlling_party_count=pipeline_report.controlling_party_count,
        controlling_parties=tuple(
            sorted(o.controlling_party for o in pipeline_report.opportunities)),
        ledger_records_written=len(pipeline_report.opportunities),
        qualified=pipeline_report.qualified,
        contracts=pipeline_report.contracts,
        cash=pipeline_report.cash,
        source_results=tuple(source_results),
    )


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    import tempfile

    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # Runnable, offline by default -- no network fetch happens here unless
    # a caller edits this to inject one, matching the discipline every
    # other __main__ entrypoint in this repository follows: this is a
    # demonstration harness, not a scheduled job. Both registered sources
    # get the same empty-OCDS-shaped stub here, so TED will correctly
    # show as UNAVAILABLE (wrong shape for its parser) -- exactly the
    # per-source isolation this module exists to make visible.
    demo_state_dir = Path(tempfile.mkdtemp()) / "opportunity_cycle_state"
    demo_ledger = OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "demo_ledger.jsonl")
    report = run_cycle(
        demo_state_dir, demo_ledger, fetch_fn=lambda: b'{"releases": []}')
    print(report.show_the_math())
