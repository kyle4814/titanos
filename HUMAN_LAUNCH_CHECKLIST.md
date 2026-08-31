# Human Launch Checklist

Everything on this list requires a human. Nothing here can be done by any
process in this repository, and no process in this repository may tick
these boxes — `kpm/promotion/state_machine.py::SelfPromotionForbidden`
exists to enforce that principle elsewhere, and it applies here too.

There are no hidden actions. Each item states why it exists, the exact
command, what you should see, how to undo it, and what happens if you
skip it.

Verify the state this list was written against before trusting it:

```sh
./run_all_tests.sh
python3 -m foundation.system_manifest
python3 -m foundation.launch_report
```

---

## 1. Set your public commit identity

- [ ] **Done**

**Why.** Your commits are currently authored as
`MONEYPRINTER <tech2@DESKTOP-I4QB2QL.localdomain>`. That name and that
machine hostname are published to a public repository with every commit,
and rewriting authorship afterwards means rewriting history on a repo
that is already public.

**Command**
```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**Expected result.** `git config --get user.email` prints what you set.
Future commits carry it. Past commits are unchanged.

**Rollback.** `git config --global --unset user.email`. Harmless.

**If you skip it.** Nothing breaks. Every future commit continues to
publish a machine hostname.

---

## 2. Decide the phone number in `foundation/gold_brick.py`

- [ ] **Decided — keep it**  /  - [ ] **Decided — remove it**

**Why.** `foundation/gold_brick.py` embeds `+61 414 244 544` in the
`CONTACT` dict, and `GoldBrick.render()` prints it into every rendered
brick. It is already public in that source file and is now also published
inside `GOLD_BRICK_TITANOS_EMERALD.md`. This may be exactly what you
want — a contact number on a work artifact is normal — but it should be
a decision rather than a default.

**Command, if removing**
```sh
# edit foundation/gold_brick.py, CONTACT dict
python3 -m unittest foundation.tests.test_gold_brick
```

**Expected result.** Two tests assert `titanos.tech` appears in a
rendered brick; neither asserts the phone number, so removing it should
leave the suite green. Verify rather than trust that.

**Rollback.** Revert the edit; it is a one-line dict value.

**If you skip it.** The number stays published in two files and in every
brick you ever render.

---

## 3. Decide whether an autonomous entrypoint is scheduled

- [ ] **Decided — schedule it**  /  - [ ] **Decided — leave manual**

**Why.** This is the single item standing between a measured
`autonomy_ratio` of `0.0000` and any non-zero figure. Exactly one
scheduled entrypoint exists today (`foundation/cron_pulse.py`) and it is
read-only. Scheduling a mutating entrypoint means a process that commits
to git on this machine without a human present — a real consequence,
which is why it is yours and not mine.

**What the loop already bounds itself with**, so you are weighing a real
risk and not a vague one: a kill switch honoured at cycle boundaries and
mid-sleep; refusal to act on a dirty tree; refusal to act on any finding
class it does not know; a re-sweep after every fix; rollback if that
verification fails; single-pathspec commits; an `fcntl` lock preventing
concurrent instances; and an explicit "local commit only, never pushed"
guarantee.

**Command, if scheduling** (append to `crontab -e`)
```
17 * * * * cd /home/tech2/cosmic-library && /usr/bin/python3 -c \
  "import sys; sys.path.insert(0,'.'); from pathlib import Path; \
   from foundation.autonomy_loop import run_one_cycle; \
   print(run_one_cycle(Path('.')))" \
  >> /home/tech2/cosmic-library/foundation/autonomy_loop.err.log 2>&1
```
Offset to :17 so it lands after the :07 pulse rather than racing it.

**Expected result.** `foundation/autonomy_loop_log.jsonl` grows by one
receipt per hour. Most will read `CLEAN_IDLE`.

**Rollback.** `crontab -e`, delete the line. Or drop a file named
`.autonomy_stop` in the repository root — the loop honours it at the next
cycle boundary and mid-sleep.

**If you skip it.** `autonomy_ratio` stays `0.0000` and the number stays
honest. **My recommendation is to skip it for now**: the loop handles
exactly one finding class, and a scheduled process that can only correct
a number in a README has not earned standing authority to commit
unattended.

---

## 4. Sign the German Engineering sign-off

- [ ] **Done**

**Why.** `GERMAN_ENGINEERING_SIGNOFF.md` carries fifteen criteria that
pass and five that do not. Its human section is deliberately blank. A
signature you did not give would be a forged signature, and every
governing document in this repository forbids inventing one.

**Command.** Edit `GERMAN_ENGINEERING_SIGNOFF.md`, Part 2, and fill the
lines by hand.

**Expected result.** The file records who accepted the five unmet
criteria and when.

**Rollback.** Edit the file. It is a record, not a mechanism.

**If you skip it.** The repository ships with an unsigned sign-off,
which is honest and simply means nobody has accepted the known gaps.

---

## 5. Release

- [ ] **Done**

**Why.** Publishing is an outward-facing, effectively irreversible act on
a public repository. It stays a human action by design.

**Command**
```sh
./release.sh
```

**Expected result.** A pre-flight report: repository state, a real test
run, a secret scan, the state digest and receipt head, launch criteria,
signing detection, and this checklist's open items. It then asks you to
type `RELEASE`. It performs exactly two actions — `git push` and printing
the resulting revision — and refuses on any failing check.

It will never create or read a private key, never sign on your behalf,
never force-push, never rewrite history, and never delete evidence.

**Rollback.** A push to a public repository cannot be meaningfully
undone. That is why it is behind a typed confirmation.

**If you skip it.** Work stays local. Nothing is lost.

---

## What is deliberately NOT on this list

These were considered and are handled by code, not by you:

- Running the tests — `./run_all_tests.sh`, and `release.sh` runs it.
- Checking for secrets — the scanner runs in pre-flight.
- Correcting README's test count — `autonomy_loop.py` owns that, with
  verification, rollback and a receipt.
- Regenerating the launch artifacts — `foundation/launch_report.py`
  computes them.
- Deciding launch status — derived from criteria, never chosen.

If a future version of this checklist asks you to do something a program
could do reliably, that is a defect in the program, not a task for you.
