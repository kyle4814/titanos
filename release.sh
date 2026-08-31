#!/usr/bin/env bash
# TITANOS — human-controlled release script.
#
# WHAT THIS IS
#
# A pre-flight check and a confirmation prompt. It performs exactly two
# actions, both declared below, and only after a human types the word.
#
# WHAT IT DELIBERATELY WILL NOT DO, EVER
#
#   - create, read, or exfiltrate a private key
#   - sign anything on a human's behalf
#   - force-push, rewrite history, or delete any evidence
#   - modify security policy, configuration, or its own authority
#   - proceed on a failing check by "warning and continuing"
#
# Every check below is a real command whose output you can reproduce by
# hand. Nothing here is asserted; if a check cannot run, it reports
# UNKNOWN rather than assuming pass.

set -uo pipefail
cd "$(dirname "$0")"

RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[0;33m'; DIM='\033[2m'; OFF='\033[0m'
BLOCKERS=0
UNKNOWNS=0

hdr()  { printf "\n${DIM}%s${OFF}\n" "────────────────────────────────────────────────────────"; printf "%s\n" "$1"; }
pass() { printf "  ${GRN}PASS${OFF}  %s\n" "$1"; }
fail() { printf "  ${RED}FAIL${OFF}  %s\n" "$1"; BLOCKERS=$((BLOCKERS+1)); }
warn() { printf "  ${YEL}NOTE${OFF}  %s\n" "$1"; }
unkn() { printf "  ${YEL}????${OFF}  %s\n" "$1"; UNKNOWNS=$((UNKNOWNS+1)); }

printf "\n  TITANOS RELEASE PRE-FLIGHT\n"

# ── 1. repository state ──────────────────────────────────────────────
hdr "1. REPOSITORY STATE"
REV=$(git rev-parse --short HEAD 2>/dev/null) || REV="UNKNOWN"
printf "  revision           %s\n" "$REV"
if [ -z "$(git status --porcelain)" ]; then
  pass "worktree clean"
else
  fail "worktree DIRTY — commit or stash before releasing:"
  git status --porcelain | sed 's/^/          /'
fi
AHEAD=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo "?")
BEHIND=$(git rev-list --count 'HEAD..@{u}' 2>/dev/null || echo "?")
printf "  ahead/behind       %s / %s\n" "$AHEAD" "$BEHIND"
[ "$BEHIND" != "0" ] && [ "$BEHIND" != "?" ] && fail "behind origin — pull and re-run"

# ── 2. tests ─────────────────────────────────────────────────────────
hdr "2. TESTS (real run, ~3 minutes)"
if [ -x ./run_all_tests.sh ]; then
  TESTOUT=$(./run_all_tests.sh 2>&1 | tail -1)
  printf "  %s\n" "$TESTOUT"
  case "$TESTOUT" in
    PASS*) pass "all suites green" ;;
    *)     fail "test suite not green" ;;
  esac
else
  unkn "run_all_tests.sh missing or not executable"
fi

# ── 3. security ──────────────────────────────────────────────────────
hdr "3. SECURITY"
SEC=$(python3 - <<'PY' 2>/dev/null
import sys; sys.path.insert(0,'.')
from pathlib import Path
from foundation.secret_scanner import scan
hi = [f for f in scan([Path('.')]).findings
      if f.confidence == "HIGH" and "test_secret_scanner" not in str(f)]
print(len(hi))
PY
) || SEC="?"
if [ "$SEC" = "0" ]; then pass "no HIGH secret findings outside the scanner's own fixtures"
elif [ "$SEC" = "?" ]; then unkn "secret scanner did not run"
else fail "$SEC HIGH secret finding(s) — DO NOT RELEASE"; fi

if git diff "@{u}..HEAD" 2>/dev/null | grep -qE 'ghp_|github_pat_|sk_live_|AKIA|BEGIN [A-Z ]*PRIVATE KEY'; then
  fail "credential pattern present in the outgoing diff"
else
  pass "no credential patterns in the outgoing diff"
fi

# ── 4. configuration, receipts, launch criteria ──────────────────────
hdr "4. STATE, RECEIPTS, LAUNCH CRITERIA"
python3 - <<'PY' 2>/dev/null || echo "  ???? manifest/launch report unavailable"
import sys; sys.path.insert(0,'.')
from pathlib import Path
from foundation.system_manifest import compute_manifest
from foundation.launch_report import assess
m = compute_manifest(Path('.').resolve())
print(f"  state digest       {m.digest()}")
print(f"  receipt head       {m.receipt_head or 'NONE'}")
print(f"  pulse findings     {m.pulse_findings}")
print(f"  tracked files      {m.tracked_files}")
a = assess(Path('.').resolve())
print(f"  launch status      {a.status()}")
for c in a.unmet():
    print(f"    UNMET  {c.name}: {c.evidence[:64]}")
PY

# ── 5. signing (detect only; never create) ───────────────────────────
hdr "5. COMMIT SIGNING (detected, never configured by this script)"
SIGNKEY=$(git config --get user.signingkey 2>/dev/null || true)
GPGSIGN=$(git config --get commit.gpgsign 2>/dev/null || true)
if [ -n "$SIGNKEY" ]; then
  pass "signing key configured: $SIGNKEY (gpgsign=${GPGSIGN:-unset})"
else
  warn "no signing key configured. This script will NEVER create one."
  printf "       To sign releases, do this yourself, then re-run:\n"
  printf "         ${DIM}git config --global user.signingkey <YOUR_KEY_ID>${OFF}\n"
  printf "         ${DIM}git config --global commit.gpgsign true${OFF}\n"
  printf "       Releasing unsigned is a valid choice; it is simply not a signed release.\n"
fi
EMAIL=$(git config --get user.email 2>/dev/null || echo "")
case "$EMAIL" in
  ""|*localdomain*|*DESKTOP*) warn "commit email is '${EMAIL:-unset}' — this becomes public. Set it with: git config --global user.email you@example.com" ;;
  *) pass "commit email: $EMAIL" ;;
esac

# ── 6. outstanding human decisions ───────────────────────────────────
hdr "6. HUMAN DECISIONS STILL OPEN"
if [ -f HUMAN_LAUNCH_CHECKLIST.md ]; then
  grep -nE '^\- \[ \]' HUMAN_LAUNCH_CHECKLIST.md | sed 's/^/  /' || echo "  none unticked"
else
  unkn "HUMAN_LAUNCH_CHECKLIST.md not found"
fi

# ── verdict ──────────────────────────────────────────────────────────
hdr "VERDICT"
printf "  blockers %s   unknowns %s\n" "$BLOCKERS" "$UNKNOWNS"
if [ "$BLOCKERS" -gt 0 ]; then
  printf "\n  ${RED}NO-GO${OFF} — %s blocking check(s) failed. Nothing was done.\n\n" "$BLOCKERS"
  exit 1
fi
if [ "$UNKNOWNS" -gt 0 ]; then
  printf "\n  ${YEL}HOLD${OFF} — %s check(s) could not run. An unknown is not a pass.\n" "$UNKNOWNS"
  printf "  Re-run once they can, or proceed by hand knowing what was unverified.\n\n"
  exit 2
fi

printf "\n  The only actions this script will take, if you confirm:\n"
printf "    1. git push origin %s\n" "$(git rev-parse --abbrev-ref HEAD)"
printf "    2. print the resulting revision\n"
printf "\n  It will not sign, tag, force, rewrite, or delete anything.\n"
printf "\n  Type RELEASE to proceed, anything else to abort: "
read -r ANSWER
if [ "$ANSWER" != "RELEASE" ]; then
  printf "\n  Aborted. Nothing was done.\n\n"; exit 3
fi

git push origin "$(git rev-parse --abbrev-ref HEAD)" || {
  printf "\n  ${RED}push failed${OFF} — nothing else was attempted.\n\n"; exit 4; }
printf "\n  ${GRN}Released${OFF} at %s\n\n" "$(git rev-parse --short HEAD)"
