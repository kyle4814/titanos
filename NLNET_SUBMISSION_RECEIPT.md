# RECEIPT — NLnet grant application submitted

**This is a real external event.** The first grant application from this
project was submitted to, and recorded by, NLnet. Recorded here as durable
provenance, tagged honestly: **SUBMITTED ≠ FUNDED.** No money is won; the
outcome is pending NLnet's review.

| Field | Value |
|---|---|
| Application code | **2026-11-076** |
| Project name | SpoofGuard — a free, self-hostable checker that tells any organisation if their email can be spoofed |
| Fund | Restack Fund |
| Requested amount | € 30,000 |
| Entity | Individual |
| Country | AU |
| Applicant | Kyle Graham |
| Project links | https://titanos.tech · https://github.com/kyle4814/titanos |
| Submitted | 2026-09-06 |
| Call deadline | 2026-11-03 (this call) |
| Status | **SUBMITTED — recorded by NLnet.** Outcome PENDING. |

(Applicant phone/email were entered on the NLnet form; deliberately NOT
committed here, since this repository is public.)

## What this is, honestly

- A real application to a real funder was completed and accepted for review.
  That is a genuine external ping — the first this project has produced that
  reaches a funding body, not an internal metric.
- It is **not** revenue, **not** a grant awarded, **not** a commitment of any
  kind by NLnet. Recording it as anything more than "submitted, under review"
  would be the exact forward-looking overclaim the reality-yield discipline
  forbids.

## What backs the application

- Working prototype in this repository: `foundation/email_security_report.py`
  (SPF/DMARC/DKIM/DNSSEC/MTA-STS posture check, A–D grade, remediation),
  `foundation/spoofguard_monitor.py` (regression monitoring),
  `leads --from-csv` / `triage_domains` (batch), documented in `SPOOFGUARD.md`.
- The honesty property the application leans on is enforced in code: a failed
  DNS lookup is UNKNOWN, never scored as a finding
  (`TestLookupFailureIsUnknownNotAbsent`, `TestFailedLookupNeverBecomesALead`).

## Next real event

NLnet's review decision. Nothing to do until then except keep the prototype
green and improve it. No follow-up contact is owed or should be initiated
unless NLnet asks.
