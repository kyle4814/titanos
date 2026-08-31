#!/usr/bin/env bash
# Aggregate test runner. One command, one summary line.
#
# WHY THIS EXISTS: a fresh engineer auditing this repository could not
# tell "slow but normal" from "hung" -- foundation/ alone exceeded a
# 60-second timeout for them, and README only gave a shell loop with no
# expected runtime and no aggregate result. That is a real onboarding
# defect, reported by a cleanroom reconstruction test on 2026-09-01.
#
# foundation/ is the slow one (~90s) and that is EXPECTED: it contains
# sigil.py's real-repository tests, and compute_sigil()'s PROOF
# dimension genuinely shells out to run every subsystem's suite. It is
# doing real work, not hanging.
set -uo pipefail
cd "$(dirname "$0")"
# Must match .github/workflows' matrix exactly. They diverged once:
# CI ran gems/claim_ledger and this file did not, so a local 'all
# green' could differ from CI's. Add a suite to BOTH or neither.
SUITES=(schema firewall kpm magl rpa taal foundation narrative compiler
        legacy gems/claim_ledger provenance)
total=0; failed=""
printf "%-12s %8s %10s\n" SUITE TESTS RESULT
printf -- "----------------------------------\n"
for s in "${SUITES[@]}"; do
  [ -d "$s" ] || continue
  start=$(date +%s)
  # Read the summary from STDERR ONLY. unittest writes "Ran N tests" and
  # "OK"/"FAILED" to stderr; a test's own print() goes to stdout, which is
  # block-buffered when piped and therefore flushes AFTER stderr at process
  # exit. Merging them with 2>&1 put a compiler test's JSON output last, so
  # `tail` never saw the summary: 41 passing tests were reported as
  # "0 FAIL" and dropped from the total. release.sh gates on this script's
  # verdict, so a parser that can be displaced by arbitrary test output is
  # not a test result -- it is a coin flip that usually lands right.
  out=$(python3 -m unittest discover -s "$s" 2>&1 1>/dev/null | tail -4)
  el=$(( $(date +%s) - start ))
  n=$(echo "$out" | grep -oE 'Ran [0-9]+' | grep -oE '[0-9]+' || echo 0)
  if echo "$out" | grep -qE '^OK'; then r="OK"; else r="FAIL"; failed="$failed $s"; fi
  printf "%-12s %8s %7s %3ss\n" "$s" "$n" "$r" "$el"
  total=$(( total + n ))
done
printf -- "----------------------------------\n"
if [ -z "$failed" ]; then
  echo "PASS  $total tests, ${#SUITES[@]} suites, 0 failures"; exit 0
else
  echo "FAIL  $total tests; failing suites:$failed"; exit 1
fi
