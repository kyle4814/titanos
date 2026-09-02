# How to run this

This page is for the operator, not a developer. It shows the exact
commands to type, what each one prints, and what to do with the output.
Nothing here requires writing or reading Python.

Run every command from the repository root (the folder this file is in).

## 0. First-time setup: tell the system who you are

The system reads your real business details from a file called
`operator_profile.json`, which does **not** exist yet on a fresh
checkout (it holds your own data, so it is never shared or committed).

Copy the example and edit it:

```
cp operator_profile.example.json operator_profile.json
```

Open `operator_profile.json` in any text editor and fill in your real
staff count, certifications, insurance, past references, and languages.
Every field is explained in the file itself (the lines starting with
`_` are documentation, not data — leave them alone or delete them).

Until you do this, every command below still runs — it just tells you,
loudly, that it's using placeholder example data instead of yours.

Check what the system currently thinks your profile is at any time:

```
python3 -m foundation.operator_cli profile
```

This prints your name, staff count, certifications, insurance,
references, languages, and the extra business facts used for supplier
registrations (ABN, ACN, address, etc.). No network. Nothing to break.

## 1. Run one hunt

```
python3 -m foundation.operator_cli hunt
```

By default this is a **dry run** — it tells you exactly what it *would*
fetch (which keyword, which sources, how big a request) and fetches
nothing. This is always safe to run.

When you're ready to actually check for real notices:

```
python3 -m foundation.operator_cli hunt --live
```

This fetches from three public procurement sources (EU TED, NZ GETS, UK
Contracts Finder), checks each notice against your operator profile, and
prints every notice it found, sorted so the most useful ones are on top:

- **QUALIFIED** — nothing published blocks you from this one.
- **INSUFFICIENT_DATA** — the notice doesn't publish enough to tell.
  Open the linked document to find out.
- **DISQUALIFIED** — a specific published clause blocks you. The exact
  clause is quoted so you can check it yourself.

**None of this is a bid recommendation.** A `QUALIFIED` band means no
published rule stops you from applying — it is not a prediction you'll
win, and it is not revenue.

If nothing was found, it says so plainly ("No notice was assessed.
That is a real result, not an error.") and exits successfully — an
empty result is not a failure.

Useful options:

```
python3 -m foundation.operator_cli hunt --live --keyword "penetration testing"
python3 -m foundation.operator_cli hunt --live --print-limit 10
```

## 2. Get the morning brief

```
python3 -m foundation.operator_cli brief
```

Same dry-run-by-default rule as `hunt`. With `--live`, this runs the
same hunt but organizes the output into four sections, in the order you
should read them:

1. **ACTION REQUIRED** — closing soon (within 14 days by default).
2. **NEW SINCE LAST BRIEF** — (only shown if you've told it about a
   previous run; a plain `brief` run has no memory of "last time").
3. **UNRESOLVED** — notices you need to open a document to understand.
4. **BLOCKED** — notices you can rule out, with the exact reason.

```
python3 -m foundation.operator_cli brief --live
python3 -m foundation.operator_cli brief --live --closing-within-days 30
```

## 3. Run it unattended (the loop)

```
python3 -m foundation.operator_cli loop
```

Dry run by default, same rule. With `--live`, this repeats the hunt on a
schedule and writes a record of every cycle to
`foundation/hunt_loop_log.jsonl` — including "nothing changed" cycles,
so you have a full history, not just the interesting moments.

```
python3 -m foundation.operator_cli loop --live --interval 3600
```

This runs forever (checking every hour by default) until you stop it.
**To stop a running loop**, create an empty file called `.hunt_stop` in
the repository root:

```
touch .hunt_stop
```

The loop checks for this file before every cycle and during every wait,
so it stops within seconds. Delete `.hunt_stop` before starting the loop
again.

To run a fixed number of cycles instead of forever (useful for testing
it out):

```
python3 -m foundation.operator_cli loop --live --max-cycles 3 --interval 60
```

## 4. Build your supplier registration dossier

```
python3 -m foundation.operator_cli dossier
```

No network, always safe to run. This prints a draft answer sheet for
government supplier registrations (NSW ICT Services Scheme, UK CCS
Cyber Security Services 3 DPS, ICN Gateway, QLD Supplier Portal),
built from `operator_profile.json`.

Every fact you haven't supplied prints as the literal text
`UNKNOWN — VERIFICATION REQUIRED` — nothing is ever guessed or
invented. At the end it prints, per scheme, the exact list of facts
still missing before you could honestly submit.

**This is preparation material only.** It is marked `DRAFT` everywhere
on purpose — you transcribe it into the real government forms yourself,
verify every fact, and sign it. It is never a submission.

## Reading the output honestly

- **QUALIFIED / INSUFFICIENT_DATA / DISQUALIFIED** are statements about
  what a notice *published*, never about whether you'll win.
- **UNKNOWN deadlines are treated as urgent**, not safe — if a date
  can't be read, the system assumes you should look at it today.
- **An empty result is a real result.** "Nothing found" and "nothing
  closing soon" are both printed plainly, not treated as errors.
- Exit code `0` means the command ran successfully — including when it
  legitimately found nothing. A non-zero exit code means something
  actually went wrong (check the printed message).

## If something looks wrong

- If a command prints `NOTICE: no operator_profile.json found...`, go
  back to step 0 — you haven't set up your real profile yet.
- If `hunt --live` or `brief --live` shows a source under "skipped:",
  read the reason next to it — a single source failing (e.g. a
  temporary network problem) does not stop the other sources from
  reporting.
- `loop --live` refuses to start if it can't build a valid request — it
  will tell you exactly why rather than failing silently.

## 5. Run it on a schedule, unattended (cron)

`operator_cli loop --live` runs forever inside one terminal you have to
keep open. `foundation/scheduled_brief.py` is the alternative for a
machine that is on all the time but where nobody is watching a
terminal: it runs **one** hunt cycle, writes a dated brief file, and
exits — the right shape for cron to call repeatedly on its own clock,
the same way `foundation/cron_pulse.py` already does for this
repository's health pulse.

Try it by hand first, exactly as cron would run it:

```
python3 -m foundation.scheduled_brief
```

This reads your real `operator_profile.json` (same fallback-to-example
rule as every other command above), runs one live hunt, and:

- writes a new dated file to `briefs/brief_<UTC timestamp>.md`
- updates `briefs/LATEST.md` to match it — **always read this path**;
  it is the one stable filename that never changes, so you never have
  to know today's timestamp to check the latest result
- deletes old dated briefs beyond the last 30 (configurable — see
  below), and only files it created itself, matching its own
  `brief_YYYYMMDDTHHMMSSZ.md` pattern; nothing else in `briefs/` is
  ever touched
- appends one line to `foundation/scheduled_brief_log.jsonl`, every
  single run, including a run that finds nothing

The brief itself leads with **what changed since the last run** — new
notices, newly-closing deadlines — not a full re-dump, the same
diff-led format `operator_cli loop` already uses.

**It is safe to schedule.** Two overlapping invocations cannot both
write: the second one sees a lock file, writes no brief, and exits
cleanly (still logging a receipt that says so). A crash mid-run always
releases the lock in a `finally` block, so one bad run cannot silence
every run after it. It takes no outward action of any kind — no email,
no webhook, no application — it only ever reads notices and writes
local files under this repository.

### Installing the cron entry

**This repository does not install a crontab entry for you.** Editing
your crontab is a persistent change to your machine, and that decision
belongs to you, not to a script. To add it yourself:

```
crontab -e
```

Then add this line (runs once a day at 07:00 local time — adjust the
schedule to taste, `crontab.guru` explains the five time fields if
you want a different one):

```
0 7 * * * cd /home/tech2/cosmic-library && /usr/bin/python3 -m foundation.scheduled_brief >> foundation/scheduled_brief_cron.log 2>&1
```

Replace `/usr/bin/python3` with the output of `which python3` if it
differs, and replace the path after `cd` if this repository ever moves.
Save and exit — `crontab -e` installs it immediately; nothing further
to run.

**To stop it**, either remove the line from `crontab -e` again, or drop
the same kill-switch file the live `loop` command already uses:

```
touch .hunt_stop
```

`scheduled_brief.py` checks for `.hunt_stop` before every cycle, the
same file and the same check `operator_cli loop --live` already uses —
one kill switch, not two. Delete `.hunt_stop` to resume.

**To change how many briefs are kept**, pass `retain_count` when
calling `run_scheduled_brief_cycle()` directly from your own script —
the default is 30. There is no `--retain-count` command-line flag on
`scheduled_brief.py` itself; it takes no arguments at all, by design,
so the one line above is the entire cron contract.
