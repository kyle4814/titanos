# D-005 — Directional time comparisons: the future-dated-input class

STATUS: FIXED in `foundation/currency.py`. TWO MORE INSTANCES FOUND AND
RECORDED, NOT FIXED (out of ownership boundary this cycle). REST OF
CANDIDATE SET AUDITED CLEAN.
AGENT: ENGINEER B, TITANOS cycle 015
DATE: 2026-09-02

## THE OPEN FINDING (blue-team pass 014), CLOSED

`RateTable.is_stale()` computed:

```python
return (ref - table_date).days > STALE_AFTER_DAYS
```

This only ever checks one direction: is the table too OLD. If
`table_date` is in the future relative to `ref` (real today), the
subtraction is negative, and a negative number is never greater than
`STALE_AFTER_DAYS`. The table reports `is_stale() == False` forever.

**Reproduced live** before touching anything:

```
>>> RateTable(date_str="2027-06-01", rates={"USD": 1.1}).is_stale(today=date(2026, 9, 2))
False   # nine months in the future, reported "fresh"
```

**Fix** (`foundation/currency.py::RateTable.is_stale`, one line):

```python
return abs((ref - table_date).days) > STALE_AFTER_DAYS
```

Now both directions are bounded by `STALE_AFTER_DAYS` — a table too old
OR too far in the future is flagged, neither is silently trusted as
current.

**Regression proof the fix is load-bearing** (git stash prohibited —
copy-aside used instead): `foundation/currency.py` was copied to a
scratch path before editing. The two new tests'
assertions (`is_stale(today=...)` must be `True` for a future-dated
table) were evaluated against the pre-fix line extracted verbatim from
that scratch copy and against the post-fix line:

```
BEFORE FIX: future_dated (2027-06-01) is_stale(today=2026-09-02): False  -- test expects True
BEFORE FIX: far_future  (2026-09-10) is_stale(today=2026-08-31): False  -- test expects True
AFTER FIX:  future_dated is_stale: True
AFTER FIX:  far_future  is_stale: True
```

New tests added to `foundation/tests/test_currency.py`:
`test_future_dated_table_is_stale_not_eternally_fresh`,
`test_far_future_dated_table_is_stale`. Full suite:
`python3 -m unittest foundation.tests.test_currency` → **25 tests, OK**.

## THE CLASS

The instance above is one shape of a broader defect: a duration/staleness
check that only bounds one side of a subtraction. Two related shapes were
named in the task brief and both were checked at every candidate site:

1. **One-directional freshness** — `(now - stamp) > threshold` (or `days >
   N`) never catches `stamp` being in the future; it silently reads as
   "very fresh" instead of "impossible / suspect".
2. **Naive/aware mixing** — comparing an aware and a naive `datetime`
   either raises `TypeError` or (if one side gets silently coerced)
   compares wall-clock values across different implicit zones.
3. **Unbounded negative duration treated as valid** — a `days_remaining`
   or similar computed value going negative and being used downstream as
   if it were a normal small/large number instead of being checked
   explicitly.

## SITES AUDITED

### `foundation/opportunity_watch.py` — CLEAN
`_ensure_aware()` normalises every datetime (parsed deadline and `now`)
to UTC-aware before any comparison — this is the exact fix this
repository already applied once for the aware/naive shape. `classify_deadline()`
uses `parsed >= current` (inclusive both ends, both directions named:
FUTURE vs EXPIRED) — not a one-directional staleness check, a genuine
classification. `closing_within()` bounds both `current <= deadline <=
window_end`. No defect.

### `foundation/winnability.py` — CLEAN
`_parse_deadline()` forces `tzinfo=timezone.utc` when naive. `assess()`
does the same to its `now` before calling `_assess_deadline()`.
`_assess_deadline()` explicitly branches `days_remaining < 0` as a
BARRIER ("deadline has already passed") — this is the *other* direction
handled correctly, the mirror image of the currency.py bug, done right.
No defect.

### `foundation/mouth_ted.py` — CLEAN (with a caveat)
No local date arithmetic; deadline filtering is delegated entirely to
TED's own server-side `EXPERT_QUERY` clause
(`deadline-receipt-request >= today()`), and downstream consumption of
the `deadline` fact goes through `winnability.py` (clean, above) or
`opportunity_watch.py` (clean, above). Caveat, not a bug: this means
`mouth_ted.py` never independently re-verifies that a returned notice's
deadline is really in the future — it trusts TED's own filter with no
second check. Not the class asked for (no local future-date-passes-as-
fresh comparison exists here), so not filed as a finding, only noted.

### `foundation/tender_radar.py` — CLEAN
Stores `tenderPeriod.endDate` as a raw fact string (`deadline`); performs
no local date comparison against it. `_recency_feed_url()` computes a
`publishedFrom` filter timestamp for the outbound query, one-directional
by design (there's no "future publishedFrom" concern — it's a lower
bound sent to the remote API, not a freshness check on received data).
No defect.

### `foundation/checkpoint.py`, `foundation/outcome_ledger.py` — CLEAN
Both only stamp `_now()` at write time (`datetime.now(timezone.utc)
.isoformat()`). Neither compares a stored timestamp back against `now`
anywhere. No freshness/expiry logic exists to audit.

### `foundation/mouth_common.py` — SAME CLASS, FOUND
`_measure_continuity()` (staleness section, ~line 468-486):

```python
age_seconds = (current - parsed).total_seconds()
if age_seconds > LOG_STALE_AFTER_SECONDS:
    stale = True
```

Both sides are correctly made tz-aware first (no naive/aware defect
here), but the staleness check is one-directional: if `parsed` (the
mouth's own last-observation timestamp) is in the future relative to
`current`, `age_seconds` is negative, never exceeds the threshold, and
`stale` stays `False`. **Scenario**: a log entry written with a future
timestamp — clock skew on the box writing the log, or a corrupted/
manually-edited log record — reports the mouth as healthy/current
instead of flagging the timestamp as impossible. Lower severity than
the currency.py instance: `latest_timestamp` here is self-generated by
this repository's own `datetime.now(timezone.utc)` calls at write time
(`mouth_common.py` line ~327), not third-party feed content, so the
attack surface is clock skew / log corruption rather than a hostile
external date. **Minimum repair** (not applied — outside this cycle's
edit boundary for this file): `age_seconds = abs((current -
parsed).total_seconds())`, same shape as the currency.py fix.

### `foundation/sentinel.py` — SAME CLASS, FOUND (two sites)
Same one-directional pattern, same self-generated-timestamp caveat as
mouth_common.py above, at two call sites:
- `check_mouth_health()` pulse-staleness block, ~line 1686-1692:
  `if (current - parsed).total_seconds() > LOG_STALE_AFTER_SECONDS:`
- pulse-log staleness block, ~line 1687-1691 (`_parse_iso` +
  `age_seconds > PULSE_STALE_AFTER_SECONDS`)

Both correctly aware-normalise both sides before subtracting; both are
one-directional. Same minimum repair as mouth_common.py:
`abs(age_seconds)`.

### Beyond the named candidate list — SAME CLASS, FOUND (two sites, higher severity)
A repo-wide grep for `is_stale`/staleness arithmetic surfaced two more
implementations not in the original candidate list, both with a more
plausible future-date input than the log-timestamp sites above, because
both stamp a *world event* that can originate from parsed external
content rather than purely `datetime.now()`:

- **`foundation/signal_spine.py::Signal.is_stale()`** (~line 230-239):
  ```python
  stamp = self.event_at if self.event_at != _UNKNOWN_TIME else self.observed_at
  seen = _parse(stamp)
  ...
  return _now(now) - seen > timedelta(days=STALE_AFTER_DAYS)
  ```
  `event_at` ("when the world event happened", per the field's own
  docstring at line 172) is populated by callers, potentially from a
  parsed external date rather than a local `datetime.now()` stamp. A
  signal whose `event_at` is future-dated (bad source data, or a feed
  publishing a forward-dated article/notice) makes `_now(now) - seen`
  negative, never exceeds `STALE_AFTER_DAYS`, and `is_stale()` returns
  `False` forever — a "radar" module's own docstring at this exact
  function warns "reading a five-year-old page today does not make its
  contents current, and this is the exact way a radar lies to itself";
  a future-dated `event_at` is the same lie in the other direction, not
  currently guarded against. **Minimum repair**: `abs(_now(now) - seen)
  > timedelta(days=STALE_AFTER_DAYS)`.

- **`foundation/opportunity.py::Opportunity.is_stale()`** (~line 200-207):
  ```python
  return (now - seen) > FRESHNESS_WINDOW
  ```
  where `seen` comes from `self.observed_at`. Same one-directional
  shape; a future-dated `observed_at` reads as permanently fresh.
  **Minimum repair**: `abs(now - seen) > FRESHNESS_WINDOW`.

Neither file is this cycle's to edit (not on the named candidate list,
not `foundation/currency.py`), so both are recorded here, not patched.

## VERDICT

The finding closed in `currency.py` was not an isolated defect. The
same one-directional shape (`elapsed > threshold`, no check for
`elapsed < 0`) recurs in four more places: `mouth_common.py` (1 site),
`sentinel.py` (2 sites), `signal_spine.py` (1 site), `opportunity.py` (1
site) — five sites total beyond currency.py. All five share the same
one-line minimum repair (`abs()` around the elapsed computation). The
two log/pulse-timestamp sites (mouth_common.py, sentinel.py) have a
narrower attack surface (self-generated timestamps, clock-skew-only);
the two world-event sites (signal_spine.py, opportunity.py) have the
same externally-influenced-input shape as the currency.py bug that was
actually closed this cycle and should be prioritised first.

The aware/naive shape specifically named in the brief (the
`opportunity_watch.py` precedent) was checked at every site above and
found clean everywhere audited — every comparison site normalises both
operands to UTC-aware before subtracting. The negative-duration shape
was checked and found handled correctly in `winnability.py`
(`days_remaining < 0` branched explicitly as BARRIER). This audit did
not pad the finding list with hypotheticals: `mouth_ted.py`,
`tender_radar.py`, `checkpoint.py`, and `outcome_ledger.py` are recorded
clean because they genuinely have no local comparison logic to be wrong
in.
