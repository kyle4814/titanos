#!/usr/bin/env python3
"""Deterministic cron entry point for the existing pulse + the first mouth.

Runs foundation/sentinel.py's Level-1 checks and appends a timestamped
result to foundation/pulse_log.jsonl. Intended to be invoked by cron,
independent of any Claude Code session — this is the one piece of this
repository that runs on a real schedule regardless of whether anyone is
in a conversation with the model.

This does not act on findings. It only records them. Finding does not
equal authorization (see sentinel.py's own docstring) — a human or a
future session reads pulse_log.jsonl and decides what, if anything, to
do about what it finds.

Also runs the two existing mouths (`foundation/mouth_pypi.py`,
`foundation/mouth_github_releases.py`) — each a small GET to a public
feed, each appended to its own `foundation/mouth_<id>_log.jsonl`. Per
"one clock, many mouths, one loop": this reuses the existing cron entry
rather than adding a second scheduler or a dispatch framework — a plain
list, iterated once per tick. A single mouth's failure (network down,
unexpected exception) is caught per-mouth and logged as its own
UNAVAILABLE record — it must never prevent `pulse_sweep()` or any other
mouth from running.

For mouths that observe a real pinned dependency, also runs
`foundation/dependency_pressure.py::evaluate_dependency_pressure()` on
a CHANGED observation and appends any resulting Finding to
`foundation/dependency_pressure_log.jsonl`. This is read-only and
advisory — it never modifies `requirements.txt`.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from foundation.sentinel import pulse_sweep  # noqa: E402
from foundation import mouth_pypi, mouth_github_releases  # noqa: E402
from foundation.dependency_pressure import evaluate_dependency_pressure  # noqa: E402

LOG_PATH = REPO_ROOT / "foundation" / "pulse_log.jsonl"
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
DEPENDENCY_PRESSURE_LOG_PATH = REPO_ROOT / "foundation" / "dependency_pressure_log.jsonl"

# One clock, N mouths: each entry is (mouth_id, observe(), state_path,
# package_name_or_None). package_name is set only for mouths that
# actually observe a pinned dependency's release feed — dependency
# pressure is evaluated only for those.
MOUTHS = (
    (mouth_pypi.MOUTH_ID, mouth_pypi.observe,
     REPO_ROOT / "foundation" / "mouth_pypi_state.json", "PyYAML"),
    (mouth_github_releases.MOUTH_ID, mouth_github_releases.observe,
     REPO_ROOT / "foundation" / "mouth_github_releases_state.json", "PyYAML"),
)


def _append_jsonl(path, record) -> None:
    """Append one record, never raising.

    THE DEFECT THIS CLOSES (found by adversarial review 2026-08-28, after
    an earlier pass fixed only the FIRST write in this file): the
    per-mouth fallback write targeted the SAME log_path that had just
    failed, under the SAME failure condition, and was itself unguarded --
    so a disk-full or permission fault raised a second time, this time
    uncaught, aborting main() and stopping the MOUTHS loop. Every mouth
    after the failing one then got NO record at all that tick, not even
    UNAVAILABLE, directly contradicting this module's own docstring
    promise. `check_mouth_health()`'s staleness path would later
    misdiagnose that silence as a stopped clock rather than a write
    fault.

    A tick that cannot record something must still run everything else;
    the failure surfaces on stderr, which the live crontab redirects into
    cron_pulse.err.log and `sentinel.read_cron_stderr()` retrieves.
    """
    try:
        with path.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:  # noqa: BLE001 — see above
        print(f"could not append to {path}: {exc}", file=sys.stderr)


def main() -> int:
    # Guarded 2026-08-28, hunt-surface rotation to cron_pulse.py's own
    # entrypoint: this call was unguarded. pulse_sweep() now isolates
    # every individual check internally (a fresh hunt this same cycle
    # found and fixed the case where one check's crash took down the
    # whole sweep), so this is narrower defense-in-depth than that fix
    # was -- but the same principle this file already commits to for
    # every other component applies here too: if pulse_sweep() ever
    # raises for any reason (now or from a future check added without
    # going through its isolation), the mouths below -- which ARE
    # carefully protected -- would never run that tick.
    try:
        report = pulse_sweep(REPO_ROOT)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_finding_count": report.raw_finding_count,
            "compacted": report.compacted,
            "findings": [asdict(f) for f in report.findings],
        }
    except Exception as exc:  # noqa: BLE001 — see above
        print(f"pulse_sweep() raised, skipping pulse record this tick: {exc}", file=sys.stderr)
        record = None
    # Guarded for the same reason the per-mouth loop below is, and it was
    # not: this module's own docstring promises "a single mouth's failure
    # ... must never prevent pulse_sweep() or any other mouth from
    # running," but an unguarded write meant a disk-full or permission
    # error here aborted the ENTIRE tick before either mouth ran, leaving
    # only a stderr traceback. Found by adversarial review 2026-08-28. A
    # tick that cannot record its pulse must still run its mouths, and
    # the failure must be visible in cron_pulse.err.log (which
    # foundation/sentinel.py::read_cron_stderr() now retrieves) rather
    # than as a silent whole-tick abort. `record` is None here only when
    # pulse_sweep() itself raised (guarded above); nothing to append then.
    if record is not None:
        _append_jsonl(LOG_PATH, record)

    for mouth_id, observe_fn, state_path, package_name in MOUTHS:
        log_path = REPO_ROOT / "foundation" / f"mouth_{mouth_id}_log.jsonl"
        try:
            obs = observe_fn(state_path)
            _append_jsonl(log_path, asdict(obs))
        except Exception as exc:  # noqa: BLE001 — one mouth must never sink the pulse or another mouth
            _append_jsonl(log_path, {
                "mouth_id": mouth_id,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "status": "UNAVAILABLE",
                "error": f"unexpected exception, not a normal FetchError: {exc}",
            })
            continue

        if package_name is None:
            continue
        try:
            finding = evaluate_dependency_pressure(obs, REQUIREMENTS_PATH, package_name)
        except Exception as exc:  # noqa: BLE001 — a pressure-evaluation bug must never sink the pulse or a mouth
            finding = None
            _append_jsonl(DEPENDENCY_PRESSURE_LOG_PATH, {
                "mouth_id": mouth_id,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "error": f"dependency pressure evaluation raised: {exc}",
            })
        if finding is not None:
            _append_jsonl(DEPENDENCY_PRESSURE_LOG_PATH, {
                "mouth_id": mouth_id,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                **asdict(finding),
            })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
