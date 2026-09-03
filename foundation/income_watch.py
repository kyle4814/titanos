"""foundation/income_watch.py -- the operator-visible surface for this
repository's non-procurement income mouths (`mouth_bounty.py`,
`mouth_gigs.py`).

WHY THIS EXISTS

`AUDIT_2026_09_02.md` Finding 1: `mouth_bounty.py` and `mouth_gigs.py`
each have a real `sweep()`, real tests, and a live-verified docstring --
and zero production callers. Nothing in `sources.py`, `operator_cli.py`
or `cron_pulse.py` ever reaches either one. An operator running
`operator_cli.py hunt`/`brief`/`loop` gets no error and no hint that a
bug-bounty program or a contract gig was ever observed -- the modules
are structurally invisible.

WHY NOT THROUGH `hunt.py`/`sources.py`/`HuntReport`

`HuntReport`'s whole vocabulary is buyer procurement-selection criteria
-- staff counts, insurance cover, corporate references, PUBLISHED
eligibility codes a supplier either meets or doesn't. A bug bounty
program has none of that; a YesWeHack program or an HN hiring comment
was never issued by a buyer running a tender process, and forcing it
through `qualification.py`'s QUALIFIED/DISQUALIFIED/INSUFFICIENT_DATA
banding would produce a verdict about criteria that were never asked.
`sources.py`'s own CRITICAL HONESTY RULE (no criteria-shaped key unless
the source genuinely publishes one) already forbids exactly this --
these two mouths were deliberately kept out of that pipeline, not
overlooked by it. This module is the correct destination `AUDIT_2026_
09_02.md` itself named as future work: a report type shaped for "a
published opportunity exists", not "does this operator qualify".

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation.mouth_bounty.parse_items()` / `_default_fetch()` -- the
    real, already-gated YesWeHack fetch and parse. This module never
    re-implements bounty-program parsing and never opens a socket of
    its own; `_default_fetch()` already routes through
    `mouth_common.fetch_feed()` with `mouth_bounty.DISCOVERY_POLICY`.
  - `foundation.mouth_gigs.parse_items()` / `_default_fetch()` -- same
    reuse, for the HN "Who is hiring?" keyword search.
  - `foundation.mouth_common.FetchError` -- the one failure type a
    source's fetch/parse step can raise; treated as UNAVAILABLE for
    that source only, same discipline as every mouth's own `observe()`.

WHAT THIS DOES NOT REUSE, AND WHY

Not `mouth_common.observe()`/`MouthObservation` directly, and not
`CanonicalSignal`. Those exist for a fusion pipeline that assumes a
buyer/demand vocabulary (`opportunity.py::SOURCE_TYPES`,
`pressure_class`, `money_state` gravity toward `handoff()`) this report
deliberately does not enter -- see the "why not through hunt.py" note
above. `IncomeSignal` is a smaller, purpose-built shape: one normalised
opportunity, a payout that is either a verbatim platform-declared range
or the honest `NOT_OBSERVED` string, and nothing else. Building a
second `CanonicalSignal`-shaped thing here would blur exactly the
distinction `sources.py`'s honesty rule exists to keep sharp.

DURABLE STATE -- A REAL FILE, READ BACK FRESH

`watch()` keeps its own append-only JSONL file at `state_path`: one line
per `(source_id, identifier)` ever observed, written once, on first
sight, and never rewritten. Every call to `watch()` reads the file fresh
off disk (`_load_seen()`) -- nothing is cached in a module-level dict or
carried between calls in memory. `CLAUDE.md`'s own Durability caveat
names six modules that call themselves "append-only ledgers" while
holding nothing but an in-memory Python object, dead on ordinary process
exit -- `crystal.py`, `reality_yield_ledger.py`, `admission.py`,
`firewall/quarantine.py`, `kpm/promotion/state_machine.py`,
`narrative/store/narrative_atom_store.py`. This file is the seventh
candidate for that list only if it is ever changed to cache what it
currently always re-reads -- see `foundation/tests/test_income_watch.py`
for a test that proves durability across two calls sharing no Python
state (a fresh state dict, a fresh file handle, nothing held over).

NO OUTWARD ACTION

This module observes and reports only -- no send, no apply, no
register, no subscribe, anywhere. Structurally checked in
`foundation/tests/test_income_watch.py::TestNoOutwardAction`, the same
shape as `hunt_loop.py`'s own `TestNoOutwardAction`.

VALUE DISCIPLINE

`IncomeSignal.payout_observed` is never a fabricated number.
`_bounty_fields()` carries YesWeHack's own declared
`bounty_reward_min`/`bounty_reward_max` verbatim when the program pays
(same rule `mouth_bounty.py::bounty_signal()` already applies) and
`NOT_OBSERVED` otherwise -- never zero, never inferred. `_gig_fields()`
is always `NOT_OBSERVED`: an HN hiring comment carries no structured
rate field at all, same discipline `mouth_gigs.py`'s own value
discipline section already states. A listed program or gig is a
published opportunity, observed live at fetch time -- never income,
never a promise of income. See `render_income_watch()`'s disclaimer,
printed unconditionally, and `TestDisclaimerLanguage` in the test file,
which pins that "lead"/"guaranteed"/"earnings" never appear in rendered
output for an unworked item.

CANNOT

  - Cannot see a source this module was not given an `IncomeSource` for
    -- `default_sources()` covers exactly `mouth_bounty`/`mouth_gigs`,
    the two sources named in this build's own task. A third
    non-procurement mouth needs its own `IncomeSource` built the same
    way, not a change to this module's control flow.
  - Cannot tell a genuinely new program/gig from one that briefly
    disappeared and reappeared -- `_load_seen()` only ever grows; an
    identifier once recorded is "seen" forever, matching every mouth in
    this repository's own inability to see history beyond current
    state.
  - Cannot dedupe across a source's own internal `MOUTH_ID` change --
    keys on `(source_id, identifier)` as supplied by the caller.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence

from foundation import mouth_bounty, mouth_gigs
from foundation.mouth_common import FetchError

__all__ = [
    "BOUNTY_PROGRAM", "CONTRACT_GIG", "KINDS", "NOT_OBSERVED",
    "DECLARED_NO_BOUNTY",
    "IncomeSignal", "IncomeSource", "IncomeSourceResult", "IncomeWatchReport",
    "bounty_source", "gigs_source", "default_sources",
    "watch", "render_income_watch",
]

BOUNTY_PROGRAM = "BOUNTY_PROGRAM"
CONTRACT_GIG = "CONTRACT_GIG"
KINDS = (BOUNTY_PROGRAM, CONTRACT_GIG)

# Never a fabricated number. See module docstring's VALUE DISCIPLINE.
NOT_OBSERVED = "NOT_OBSERVED"

# THIS REPOSITORY'S OWN RULE, RUNNING BACKWARDS.
#
# Everywhere else here, the discipline is that an absent value must not
# be reported as zero: UNKNOWN is not ZERO. This module had the inverse
# defect. YesWeHack declares `bounty: false` on YesWeHack Dojo -- that
# is an OBSERVED FACT that the programme pays nothing, and it was being
# reported as NOT_OBSERVED, which says "we did not see a payout".
#
# An operator reading the report could not tell a programme that
# publishes no rate (an HN hiring comment, genuinely unknown) from one
# that explicitly states it pays nothing. Those are opposite states and
# collapsing them wastes exactly the attention this module exists to
# save. Measured live 2026-09-04: 1 of 60 programmes declares
# `bounty: false`; all 60 declare `vdp: false`.
DECLARED_NO_BOUNTY = "DECLARED_NO_BOUNTY"


def _clean_str(value: object) -> str:
    """Same discipline as every mouth's own `_clean_str`: a field this
    module does not control the type of is read as absent, never
    crashes the normalise step."""
    return value if isinstance(value, str) else ""


@dataclass(frozen=True)
class IncomeSignal:
    """One normalised opportunity from a non-procurement source.
    `payout_observed` is either a verbatim platform-declared value, or
    the literal string `NOT_OBSERVED` -- construction refuses an empty
    string so a caller cannot silently drop the field."""

    source_id: str
    identifier: str
    title: str
    url: str
    kind: str
    first_seen: str
    payout_observed: str = NOT_OBSERVED

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(
                f"IncomeSignal.kind must be one of {KINDS}, got {self.kind!r}")
        if not self.identifier:
            raise ValueError("IncomeSignal.identifier must not be empty")
        if not self.payout_observed:
            raise ValueError(
                "IncomeSignal.payout_observed must never be empty -- use "
                f"{NOT_OBSERVED!r} explicitly rather than a fabricated or "
                "blank value")


@dataclass(frozen=True)
class IncomeSource:
    """One mouth adapted into this module's shape. `fetch_fn`/`parse_fn`
    are injected in every test in `foundation/tests/test_income_watch.py`
    -- no test touches the real network. Production defaults
    (`bounty_source()`/`gigs_source()`) point at the real mouths' own
    already-gated `_default_fetch()`, so this module opens no socket of
    its own."""

    source_id: str
    kind: str
    fetch_fn: Callable[[], bytes]
    parse_fn: Callable[[bytes], tuple[dict, ...]]
    # item dict -> {"identifier", "title", "url", "payout_observed"}
    to_fields: Callable[[dict], dict]


def _bounty_fields(item: dict) -> dict:
    """One `mouth_bounty.parse_items()` item -> income_watch fields.
    Reward range carried verbatim only when the program genuinely pays
    -- same `is_paying` test `mouth_bounty.py::bounty_signal()` already
    uses, never re-derived differently here."""
    slug = _clean_str(item.get("slug")).strip()
    title = _clean_str(item.get("title")).strip() or slug
    # Three states, not two. See DECLARED_NO_BOUNTY.
    declares_no_pay = item.get("vdp") is True or item.get("bounty") is False
    has_range = isinstance(item.get("bounty_reward_max"), (int, float)) \
        and item["bounty_reward_max"] > 0
    if bool(item.get("bounty")) and has_range:
        currency = _clean_str(item.get("currency"))
        payout = f"{item.get('bounty_reward_min')}-{item.get('bounty_reward_max')} {currency}".strip()
    elif declares_no_pay:
        payout = DECLARED_NO_BOUNTY
    else:
        # Pays, but published no range -- genuinely unknown.
        payout = NOT_OBSERVED
    return {
        "identifier": slug,
        "title": title,
        "url": f"https://yeswehack.com/programs/{slug}" if slug else "",
        "payout_observed": payout,
    }


def _gig_fields(item: dict) -> dict:
    """One `mouth_gigs.parse_items()` item -> income_watch fields.
    Always `NOT_OBSERVED` -- HN hiring comments carry no structured rate
    field, see `mouth_gigs.py`'s own value discipline section."""
    object_id = _clean_str(item.get("object_id")).strip()
    comment = _clean_str(item.get("comment_text"))
    snippet = comment[:160] + ("..." if len(comment) > 160 else "")
    return {
        "identifier": object_id,
        "title": snippet or object_id,
        "url": f"https://news.ycombinator.com/item?id={object_id}" if object_id else "",
        "payout_observed": NOT_OBSERVED,
    }


def bounty_source() -> IncomeSource:
    """The real YesWeHack bounty-program source. `fetch_fn` is
    `mouth_bounty._default_fetch` -- already gated by
    `mouth_bounty.DISCOVERY_POLICY` inside `mouth_common.fetch_feed()`;
    this function does not build a second policy."""
    return IncomeSource(
        source_id=mouth_bounty.MOUTH_ID, kind=BOUNTY_PROGRAM,
        fetch_fn=mouth_bounty._default_fetch,
        parse_fn=mouth_bounty.parse_items,
        to_fields=_bounty_fields,
    )


def gigs_source() -> IncomeSource:
    """The real HN 'Who is hiring?' contract-gig source. `fetch_fn` is
    `mouth_gigs._default_fetch` -- already gated by
    `mouth_gigs.DISCOVERY_POLICY`."""
    return IncomeSource(
        source_id=mouth_gigs.MOUTH_ID, kind=CONTRACT_GIG,
        fetch_fn=mouth_gigs._default_fetch,
        parse_fn=mouth_gigs.parse_items,
        to_fields=_gig_fields,
    )


def default_sources() -> tuple[IncomeSource, ...]:
    """The standard two non-procurement income sources this build wires
    up. A third mouth needs its own `IncomeSource`, not a change here."""
    return (bounty_source(), gigs_source())


@dataclass(frozen=True)
class IncomeSourceResult:
    """Per-source outcome of one `watch()` cycle -- report only, same
    OK/UNAVAILABLE shape every mouth's own observation uses."""

    source_id: str
    kind: str
    status: str  # OK | UNAVAILABLE
    error: Optional[str]
    fetched_count: int


@dataclass(frozen=True)
class IncomeWatchReport:
    observed_at: str
    results: tuple[IncomeSourceResult, ...]
    signals: tuple[IncomeSignal, ...]
    new_signals: tuple[IncomeSignal, ...]


def _load_seen(state_path: Path) -> dict:
    """Read every prior record from the JSONL state file, fresh off
    disk -- never a module-level cache, never held between calls.
    Returns `{(source_id, identifier): first_seen}`. A missing file
    reads as "nothing seen yet"; one malformed line is skipped, never
    aborts the read of the rest -- same discipline every mouth's own
    state loader already uses for a corrupt state file."""
    seen: dict = {}
    if not state_path.exists():
        return seen
    for line in state_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        source_id = record.get("source_id")
        identifier = record.get("identifier")
        first_seen = record.get("first_seen")
        if not source_id or not identifier or not first_seen:
            continue
        seen[(source_id, identifier)] = first_seen
    return seen


def _append_seen(state_path: Path, records: Sequence[dict]) -> None:
    """Append-only: existing lines are never rewritten, never deleted.
    A no-op when there is nothing new, so an all-UNCHANGED cycle never
    touches the file."""
    if not records:
        return
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True))
            fh.write("\n")


def watch(
    sources: Sequence[IncomeSource],
    state_path: Path,
    now: Optional[datetime] = None,
) -> IncomeWatchReport:
    """One observation cycle across every non-procurement income
    source. Durable NEW-item state lives at `state_path`, a real JSONL
    file read back fresh at the start of this call -- see module
    docstring's DURABLE STATE section. Each source's own fetch is
    independently gated by its own `DiscoveryPolicy`
    (`mouth_bounty.py`/`mouth_gigs.py`) -- this function opens no
    socket itself and builds no policy of its own."""
    state_path = Path(state_path)
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    seen = _load_seen(state_path)

    results: list[IncomeSourceResult] = []
    all_signals: list[IncomeSignal] = []
    new_signals: list[IncomeSignal] = []
    new_records: list[dict] = []

    for source in sources:
        try:
            raw = source.fetch_fn()
            items = source.parse_fn(raw)
        except FetchError as exc:
            results.append(IncomeSourceResult(
                source_id=source.source_id, kind=source.kind,
                status="UNAVAILABLE", error=str(exc), fetched_count=0))
            continue

        results.append(IncomeSourceResult(
            source_id=source.source_id, kind=source.kind,
            status="OK", error=None, fetched_count=len(items)))

        for item in items:
            fields = source.to_fields(item)
            identifier = _clean_str(fields.get("identifier")).strip()
            if not identifier:
                # No stable identity to dedupe against -- dropped rather
                # than keyed on a guess, same discipline every mouth's
                # own guid-less/slug-less item handling uses.
                continue
            key = (source.source_id, identifier)
            first_seen = seen.get(key, observed_at)
            signal = IncomeSignal(
                source_id=source.source_id,
                identifier=identifier,
                title=_clean_str(fields.get("title")) or identifier,
                url=_clean_str(fields.get("url")),
                kind=source.kind,
                first_seen=first_seen,
                payout_observed=_clean_str(fields.get("payout_observed")) or NOT_OBSERVED,
            )
            all_signals.append(signal)
            if key not in seen:
                new_signals.append(signal)
                new_records.append({
                    "source_id": source.source_id,
                    "identifier": identifier,
                    "first_seen": observed_at,
                })

    _append_seen(state_path, new_records)

    return IncomeWatchReport(
        observed_at=observed_at,
        results=tuple(results),
        signals=tuple(all_signals),
        new_signals=tuple(new_signals),
    )


# Deliberately avoids "lead", "guaranteed", "earnings" -- see module
# docstring's VALUE DISCIPLINE and TestDisclaimerLanguage in the test
# file, which pins that none of those three words ever appear in
# rendered output describing an unworked item.
_DISCLAIMER = (
    "every program/gig below is a PUBLISHED OPPORTUNITY, observed live "
    "at fetch time -- it is not income and it is not a promise of "
    "income. A declared bounty range is the platform's own advertised "
    "terms, never a paid amount."
)


def _payout_column(signal: "IncomeSignal") -> str:
    """One rendering of payout, used by both blocks of the report.

    It was inlined in the NEW block only, which is how the full listing
    came to carry no payout at all -- see the note at its second call
    site. One function so the two blocks cannot drift apart again.
    """
    if signal.payout_observed == NOT_OBSERVED:
        return ""
    if signal.payout_observed == DECLARED_NO_BOUNTY:
        # Stated loudly rather than left blank: a blank reads as "rate
        # not published", the opposite of what the platform declared.
        return "  PAYS NOTHING (platform declares no bounty)"
    return f"  payout={signal.payout_observed}"


def render_income_watch(report: IncomeWatchReport, limit: Optional[int] = None) -> str:
    """Text render. NEW items lead: a newly-added bug bounty program or
    contract gig is the single highest-value signal in this lane for a
    newcomer with no reputation -- see module docstring's WHY THIS
    EXISTS and `mouth_bounty.py`'s own Adobe/Intigriti finding."""
    lines = [
        f"INCOME WATCH observed_at={report.observed_at} "
        f"sources={len(report.results)} total={len(report.signals)} "
        f"new={len(report.new_signals)}"
    ]
    for result in report.results:
        if result.status == "UNAVAILABLE":
            lines.append(f"  UNAVAILABLE  source={result.source_id}  error: {result.error}")
        else:
            lines.append(
                f"  OK  source={result.source_id}  kind={result.kind}  "
                f"fetched={result.fetched_count}")

    lines.append("")
    lines.append(_DISCLAIMER)
    lines.append("")

    if not report.new_signals:
        lines.append(
            "  zero new programs/gigs observed this cycle -- a valid, "
            "honest outcome, not an error")
    else:
        lines.append("NEW THIS CYCLE:")
        shown_new = report.new_signals[:limit] if limit else report.new_signals
        for s in shown_new:
            payout = _payout_column(s)
            lines.append(f"  NEW [{s.kind}] {s.title!r}{payout}  {s.url}")

    new_ids = {(s.source_id, s.identifier) for s in report.new_signals}
    if report.signals:
        lines.append("")
        lines.append(f"ALL CURRENTLY OBSERVED ({len(report.signals)}):")
        shown_all = report.signals[:limit] if limit else report.signals
        for s in shown_all:
            marker = "new " if (s.source_id, s.identifier) in new_ids else "seen"
            # THE PAYOUT COLUMN BELONGS HERE TOO. It was rendered only in
            # the NEW block -- and after the first run nothing is ever
            # new, so the list an operator actually scans carried no
            # payout information at all. A programme that declares it
            # pays nothing sat in it indistinguishable from one paying
            # EUR230,000.
            lines.append(f"  {marker} [{s.kind}] {s.title!r}"
                         f"{_payout_column(s)}  {s.url}")

    return "\n".join(lines)
