#!/usr/bin/env bash
# Aggregate test runner. One command, one summary line.
#
# WHY THIS EXISTS: a fresh engineer auditing this repository could not
# tell "slow but normal" from "hung" -- foundation/ alone exceeded a
# 60-second timeout for them, and README only gave a shell loop with no
# expected runtime and no aggregate result. That is a real onboarding
# defect, reported by a cleanroom reconstruction test on 2026-09-01.
#
# SPEED (2026-09-05): the 12 suites now run CONCURRENTLY, not one after
# another -- wall time is the SLOWEST suite, not the SUM. foundation/ is
# the slow pole and that is EXPECTED: it contains sigil.py's real-repo
# tests, and compute_sigil()'s PROOF dimension genuinely shells out to run
# every subsystem's suite (now itself parallel, and its determinism pair
# now computed concurrently). For the tight dev loop, `--fast` skips only
# the one ~4-minute real-repo sigil class (TITAN_SKIP_REALREPO_SIGIL=1) and
# brings the whole run under ~a minute. DEFAULT (no flag) runs everything,
# so pre-commit and CI keep full coverage -- never commit on --fast alone.
set -uo pipefail
cd "$(dirname "$0")"

FAST=0
for arg in "$@"; do
  case "$arg" in
    --fast) FAST=1 ;;
    -h|--help) echo "usage: $0 [--fast]"; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done
if [ "$FAST" = "1" ]; then export TITAN_SKIP_REALREPO_SIGIL=1; fi

# Must match .github/workflows' matrix exactly. They diverged once:
# CI ran gems/claim_ledger and this file did not, so a local 'all
# green' could differ from CI's. Add a suite to BOTH or neither.
SUITES=(schema firewall kpm magl rpa taal foundation narrative compiler
        legacy gems/claim_ledger provenance)

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Each suite writes its own stderr to a private file, and its OWN start/end so
# the per-suite time is real. We read the summary from STDERR ONLY: unittest
# writes "Ran N tests" and "OK"/"FAILED" to stderr; a test's own print() goes
# to stdout, which is block-buffered when piped and flushes AFTER stderr at
# process exit. Merging them with 2>&1 once put a compiler test's JSON output
# last, so `tail` never saw the summary and 41 passing tests were reported as
# "0 FAIL". release.sh gates on this script's verdict, so the parser must never
# be displaceable by arbitrary test output.
run_suite() {
  local s="$1" safe st
  safe=${s//\//_}
  st=$(date +%s)
  python3 -m unittest discover -s "$s" >/dev/null 2>"$work/$safe.err"
  echo "$?" >"$work/$safe.rc"; echo $(( $(date +%s) - st )) >"$work/$safe.el"
}

# The 11 LIGHT suites run concurrently among themselves. `foundation` runs
# ISOLATED afterwards, because it internally spawns its own subprocess swarm
# (the real-repo sigil PROOF shells out to run all 8 subsystem suites) — under
# concurrent load with the others that over-subscribes an 8-core box, a nested
# subprocess starves, and `all_tests_green` flips false. Diagnosed 2026-09-05:
# foundation and the real-repo sigil classes each pass ALONE; only the fully
# concurrent run flaked. Isolating foundation gives its swarm the whole box.
for s in "${SUITES[@]}"; do
  [ -d "$s" ] || continue
  [ "$s" = "foundation" ] && continue
  run_suite "$s" &
done
wait
[ -d foundation ] && run_suite foundation

printf "%-12s %8s %10s\n" SUITE TESTS RESULT
printf -- "----------------------------------\n"
total=0; failed=""
for s in "${SUITES[@]}"; do
  [ -d "$s" ] || continue
  safe=${s//\//_}
  el=$(cat "$work/$safe.el" 2>/dev/null || echo 0)
  out=$(tail -4 "$work/$safe.err" 2>/dev/null)
  rc=$(cat "$work/$safe.rc" 2>/dev/null || echo 1)
  n=$(echo "$out" | grep -oE 'Ran [0-9]+' | grep -oE '[0-9]+' || echo 0)
  # Green iff the process exited 0 AND unittest printed an OK line. Either
  # alone is insufficient: a crash before the summary exits non-zero with
  # no OK; a skip-only run still prints OK. Both must agree.
  if [ "$rc" = "0" ] && echo "$out" | grep -qE '^OK'; then r="OK"; else r="FAIL"; failed="$failed $s"; fi
  printf "%-12s %8s %7s %3ss\n" "$s" "$n" "$r" "$el"
  total=$(( total + n ))
done
printf -- "----------------------------------\n"
[ "$FAST" = "1" ] && echo "(--fast: real-repo sigil class skipped -- not for pre-commit)"
if [ -z "$failed" ]; then
  echo "PASS  $total tests, ${#SUITES[@]} suites, 0 failures"; exit 0
else
  echo "FAIL  $total tests; failing suites:$failed"; exit 1
fi
