# Capability Matrix

Generated `2026-08-31T20:39:45.496174+00:00` at revision `083a71d` (state digest `4a12489fae042d5d`).

**Generated file — do not hand-edit.** Regenerate with `python3 -m foundation.launch_report`.

| Criterion | State | Evidence |
|---|---|---|
| TESTS_GREEN | **MET** | 2690 run, 0 failed |
| WORKTREE_CLEAN | **UNMET** | git status --porcelain non-empty |
| PULSE_CLEAN | **MET** | sentinel.pulse_sweep() -> 0 finding(s) |
| NETWORK_GATED | **MET** | fetch_feed() calls authorize_discovery() before urlopen |
| RECEIPT_CHAIN | **MET** | outcome ledger present; head OC-eecf6388ada2d538 |
| CHECKPOINT_ENGINE | **MET** | foundation/checkpoint.py |
| WRITE_SCOPE_ENFORCED | **MET** | foundation/write_scope.py |
| RADAR_RAIL_WIRED | **MET** | foundation/radar_rail.py composes mouth->tentacle->report |
| AUTONOMY_MEASURED | **MET** | autonomy_ratio=0.0000 (measured, not claimed) |
| AUTONOMY_ACHIEVED | **UNMET** | autonomy_ratio=0.0000; no scheduled mutating entrypoint |
| COMMERCIAL_OUTCOME | **UNMET** | pipeline 0, contracts 0, cash 0 -- no external outcome has ever been observed |

**3 of 11 criteria unmet.** Status: `READY_WITH_LIMITATIONS`.
