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
