#!/usr/bin/env python3
"""Cron-shaped entry point for foundation/authority_runtime.py, mirroring
foundation/cron_pulse.py's exact proven shape: a thin main() a real
scheduler can invoke once per trigger, independent of any Claude Code
session.

THE EXACT GAP THIS CLOSES

foundation/authority_runtime.py's tick() and run_loop() were proven
correct in bounded, manually-invoked test/soak runs -- but nothing in
this repository could actually be pointed at by cron, because neither
authority_runtime.py nor authority_sigil.py had an `if __name__ ==
"__main__":` entry point. This script is that bridge, and nothing else.

WHY THIS SCRIPT IS SAFE TO ADD WITHOUT INSTALLING ANYTHING LIVE

Unlike cron_pulse.py (already a real, live crontab entry), nothing in
this repository invokes this script yet -- adding it changes nothing
about what actually runs on this machine. It also targets
RELEASE_ID = "PULSE_AUTHORITY_001" against the real, default
foundation/authority_ledger.jsonl -- and no release under that id has
been issued there. Run today, this script's real, single behavior is:
authorize_action() correctly returns DENY ("release_id ... does not
exist"), tick() writes a receipt saying so, and the script exits 0. It
is inert by construction until a human separately issues a real release
via foundation.authority_sigil.issue_release() -- the same two-step
separation (build the door, then separately decide to walk through it)
already used for foundation/discovery_authorization.py this same
session.

WHAT THIS SCRIPT DOES NOT DO

It does not loop. It does not install a crontab entry. It does not
issue a release. It performs exactly one tick() and exits -- real
recurrence, if ever separately authorized, is a scheduler (cron,
matching this repository's only existing precedent) invoking this
script repeatedly, the same relationship cron already has with
cron_pulse.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from foundation.authority_runtime import tick  # noqa: E402
from foundation.authority_sigil import ReleaseLedger  # noqa: E402

# Matches authority_sigil.py's/authority_runtime.py's own module
# defaults -- named here explicitly rather than imported, so this
# script's real target is legible without reading two other files.
LEDGER_PATH = REPO_ROOT / "foundation" / "authority_ledger.jsonl"
TICK_LOG_PATH = REPO_ROOT / "foundation" / "authority_runtime_tick_log.jsonl"
RELEASE_ID = "PULSE_AUTHORITY_001"


def main() -> int:
    ledger = ReleaseLedger(ledger_path=LEDGER_PATH)
    result = tick(ledger, RELEASE_ID, str(REPO_ROOT), log_path=TICK_LOG_PATH)
    # Both ADMIT and DENY are valid, receipted, expected outcomes --
    # same "finding does not equal authorization, and a denial is not a
    # script failure" discipline as cron_pulse.py's own mouths. Only an
    # actual unhandled exception should ever produce a non-zero exit.
    print(f"authority_pulse tick: admitted={result.admitted} reasons={result.reasons}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
