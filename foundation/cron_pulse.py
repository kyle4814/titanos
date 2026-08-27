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


def main() -> int:
    report = pulse_sweep(REPO_ROOT)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_finding_count": report.raw_finding_count,
        "compacted": report.compacted,
        "findings": [asdict(f) for f in report.findings],
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")

    for mouth_id, observe_fn, state_path, package_name in MOUTHS:
        log_path = REPO_ROOT / "foundation" / f"mouth_{mouth_id}_log.jsonl"
        try:
            obs = observe_fn(state_path)
            with log_path.open("a") as f:
                f.write(json.dumps(asdict(obs)) + "\n")
        except Exception as exc:  # noqa: BLE001 — one mouth must never sink the pulse or another mouth
            with log_path.open("a") as f:
                f.write(json.dumps({
                    "mouth_id": mouth_id,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "UNAVAILABLE",
                    "error": f"unexpected exception, not a normal FetchError: {exc}",
                }) + "\n")
            continue

        if package_name is None:
            continue
        try:
            finding = evaluate_dependency_pressure(obs, REQUIREMENTS_PATH, package_name)
        except Exception as exc:  # noqa: BLE001 — a pressure-evaluation bug must never sink the pulse or a mouth
            finding = None
            with DEPENDENCY_PRESSURE_LOG_PATH.open("a") as f:
                f.write(json.dumps({
                    "mouth_id": mouth_id,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "error": f"dependency pressure evaluation raised: {exc}",
                }) + "\n")
        if finding is not None:
            with DEPENDENCY_PRESSURE_LOG_PATH.open("a") as f:
                f.write(json.dumps({
                    "mouth_id": mouth_id,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    **asdict(finding),
                }) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
