# UK_SUBTHRESHOLD.md — reaching the sub-£30k UK band, properly

**Sweep date:** 2026-09-02, one throttled live run against UK Contracts
Finder's OCDS Search API (~1 request per 42 seconds, 17 requests total,
zero 429s). Script: `/tmp/claude-1000/-home-tech2/7a233700-c5d0-42b0-a73b-54c78cec2146/scratchpad/cf_probe.py`.
Raw output: `cf_probe.jsonl` (parameter tests), `cf_sweep.jsonl` (per-window
counts), `cf_candidates.json` (extracted candidates) in the same directory.
No `.py` file outside `foundation/tender_radar.py` was touched. Full
`foundation` regression run afterward.

## PART 1 — THE PAGINATION QUESTION IS ANSWERED, AND THE PRIOR ASSUMPTION WAS WRONG

Prior recon (2026-09-01, in `tender_radar.py`'s own module docstring) proved
`publishedFrom`/`publishedTo` genuinely filter, and separately proved CPV and
eleven keyword-parameter names are all silently ignored (garbage in →
identical 100-release result set). It never tested `stages`, `limit`, or
`cursor` against a nonsense value the same way — so `SMALL_CONTRACTS.md`'s
"this module cannot paginate past page 1 (proven dead)" was resting on an
untested gap, not a completed proof.

Tested live 2026-09-02, same discipline (nonsense value vs. no value vs. real
value, comparing the real result set/behaviour, not just a count):

| Parameter | Nonsense value | Real value | Verdict |
|---|---|---|---|
| `cursor` | `cursor=nonsense12345` → **HTTP 400 Bad Request** | value read from the baseline response's own `links.next` field → HTTP 200, a **disjoint** set of 100 releases (zero overlap with page 1 in the sampled ocids) | REAL, validated forward pagination |
| `stages` | `stages=xyzzy123` → **HTTP 400 Bad Request** | `stages=tender` → HTTP 200, tag mix changed from `{award:89, tender:5, awardUpdate:5, planning:1}` to `{tender:82, tenderAmendment:18}` | REAL, validated filter |
| `limit` | `limit=notanumber` → **HTTP 400 Bad Request** | `limit=20` → HTTP 200, exactly 20 releases returned (vs. 100 with none) | REAL, validated |

This is the **opposite failure mode** from CPV/keyword: those two are
silently accepted and ignored on garbage input (200, identical result). All
three of `stages`/`limit`/`cursor` **reject** garbage with 400 — direct
evidence the server actually parses and enforces them, corroborated by the
real-value behaviour change in every case. `tender_radar.py` has been
updated accordingly:

- `_recency_feed_url()` now appends `&stages=tender` by default
  (`STAGES_TENDER_ONLY = "tender"`) — a verified efficiency gain (server
  drops award/awardUpdate/planning noise before the wire), not a new
  filtering behaviour (the module already discarded those client-side).
- `_next_cursor_url(raw)` reads the real `links.next` field for a caller
  that wants to walk further pages. Not wired into `observe()`/`sweep()`'s
  default single-fetch cycle (kept "one bounded request per call," the same
  discipline every mouth here uses) — this sweep called it directly, from a
  throttled one-off script, the same way `SMALL_CONTRACTS.md`'s prior sweep
  was run without editing a mouth's default behaviour.

16 new offline tests added (`TestStagesParamDefault`, `TestNextCursorUrl`) —
**70/70 `test_tender_radar.py` passing**, real count, run this cycle.

## PART 2 — THE 60-DAY SWEEP

Rather than trust `cursor` alone (one page ≈ 100 releases, and daily publish
volume is roughly 12–17 releases/day at this endpoint's current rate — a
single page would not reliably cover 60 days), the sweep used
`publishedFrom`/`publishedTo` date-window slicing: ten 6-day windows walking
back from 2026-09-02 to 2026-07-04, `size=100` per window, one request per
window, ~42s apart.

**Every window returned under the 100-release cap** (95–99 releases each) —
no window was truncated, so this sweep did not silently miss releases inside
its own 60-day span from hitting the page-size ceiling.

**Result: 62 unique genuinely-open notices** (`tag` includes `"tender"`,
`tender.status` in `active`/`planning`) across the full 60-day window — more
than **12× the 5 open notices** the prior single-page sweep saw, because that
sweep's one page was dominated by award notices from the last few days, not
because a different population of notices exists.

## PART 3 — CLIENT-SIDE FILTERING, HONEST RESULTS

Filtered the 62 open items two ways: (a) title/description/CPV text against
a security/IT keyword list, (b) `tender.value.amount < £30,000` with
`currency == "GBP"`. **4 hits each** (8 total, no overlap). Checked each
against **today's date (2026-09-02)** for whether it is still actually open,
since a notice can be OBSERVED as open at publish time and have since closed.

### Security-keyword hits (4) — most are false positives, stated honestly

| Title | Buyer | Value | Deadline | Still open? | Notes |
|---|---|---|---|---|---|
| [RA359859 – Security and Fire Maintenance](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/f84c20c3-3fd1-4f3b-b0a6-9004499479fe-912183) | NHS Wales Shared Services Partnership | not stated | 2026-08-28 | **No — closed** | Genuine security-relevant notice; deadline passed before this sweep ran. Response required via MultiQuote portal registration. |
| [CA18385 – Nova Education Trust: IT Security and Internet Filtering Platform](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/9a73e058-dc64-4818-a6d0-0e029307679b-912138) | Nova Education Trust | £500,000 | 2026-09-28 | **Yes** | Real, open, genuinely IT/cyber-security work (firewall, endpoint, managed threat detection, ~5,000 endpoints). **Not sub-threshold** — £500k is well above the £30k target band and this scale of engagement is not realistic for a solo operator. Response via MultiQuote. |
| Castle Ward Woodland Restoration (National Trust NI) | The National Trust | £100,000 | 2026-08-10 | No — closed | **False positive** — matched on "the primary **threat** to the woodland" (invasive species). Not security work. |
| Elvetham Heath Parish Council MUGA extension | Elvetham Heath Parish Council | £40,000 | 2026-08-09 | No — closed | **False positive** — matched on "**Security** fencing is required" (a physical-fencing line item in a playground-equipment tender, not IT/cyber security). |

### Low-value hits, under £30,000 (4) — none are security work

| Title | Buyer | Value | Deadline | Still open? | Security-relevant? |
|---|---|---|---|---|---|
| [CA18403 – RFQ 2026/32 – PR Agent for DTFF Celebration Event](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/0b75532b-8448-4ce1-bc1d-f54027d14a57-912634) | Newry, Mourne and Down District Council | £29,500 | 2026-09-15 | **Yes** | No — PR/events agency |
| [Electrical & Mechanical Consultancy Services for Generator Infrastructure](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/18036e22-d57b-48e2-b80f-8929f1f72af5-910915) | Civil Nuclear Police Authority / Civil Nuclear Constabulary | £20,000 | 2026-09-07 | **Yes** | No — buyer is a policing/nuclear-security body, but the scope of work itself is electrical/mechanical engineering consultancy, not IT/cyber security. Included because the buyer identity is worth knowing, not because the work matches. |
| Procurement of IT-equipment and UAVs | Chemonics International (Partnership Fund for a Resilient Ukraine) | £1 (placeholder) | 2026-08-25 | No — closed | No — IT hardware/UAV procurement, not security services; £1 is a nominal/framework placeholder, not a real value |
| Group learning module on urban nature finance | The National Trust | £20,000 | 2026-07-31 | No — closed | No |

**No qualification/pre-registration requirement was stated as a barrier on
any of these beyond the platform-level MultiQuote/Proactis Plaza account
registration** several buyers route through (a free-registration soft
barrier, not a corporate prequalification questionnaire) — none of the eight
notices name insurance, turnover, past-performance, or accreditation
requirements in their text.

## THE HONEST HEADLINE

**Zero notices matched all three criteria at once: genuinely open today,
under £30,000, and IT/cyber-security work.** That is a real result from a
methodologically correct 60-day sweep (validated cursor/stages/limit
parameters, no rate-limit violations, client-side keyword+value filtering,
today's-date open-check applied), not a tooling failure — the prior sweep's
negative result was real too, it was just drawn from a much smaller, biased
sample (page 1, dominated by awards).

The two closest partial matches, reported honestly rather than stretched to
fit:

- **CA18385 (Nova Education Trust IT Security)** — real, open, genuinely
  security work — but at £500,000, roughly 17× above the sub-threshold
  target band.
- **CA18403 (PR Agent, £29,500)** and the **Generator Infrastructure
  consultancy (£20,000, Civil Nuclear Police Authority)** — both genuinely
  open and genuinely sub-threshold — but neither is security/IT work.

## WHAT WOULD ACTUALLY CLOSE THIS GAP NEXT

The now-proven `_next_cursor_url()` + `stages=tender` capability makes a
**longer** sweep (90+ days, or a standing weekly cursor-walk) cheap to run
with the same throttle discipline — the ceiling on catching a genuine
sub-£30k security notice is sample size and publish-rate luck, not the API.
At roughly 4–6 tender-tagged releases/day and maybe one in twenty carrying a
security keyword, a single sub-threshold security hit landing inside any
given 60-day window is a real possibility, not a certainty — this sweep's
honest negative result says "not this window," not "never." A recurring
weekly sweep (reusing `_next_cursor_url()`, throttled, one page per run)
would accumulate coverage instead of re-sampling the same recent window each
time.
