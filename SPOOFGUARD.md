# SpoofGuard

**A free, self-hostable checker that tells any organisation whether their email
can be spoofed — and exactly how to fix it.**

Most small organisations have email that can be forged in their name: their
domain is missing or misconfiguring the standards that stop spoofing (SPF,
DMARC, DKIM, DNSSEC, MTA-STS). Criminals exploit this for invoice fraud and
phishing against the organisation's own customers. SpoofGuard checks a domain's
public email-security posture, grades it, tells a non-expert precisely what to
fix, and keeps watching so it never silently regresses.

This is the working prototype behind an NGI Zero / NLnet grant application. The
engine described below runs today; the grant hardens it into a fully packaged,
documented, self-hostable tool for the commons.

## What makes it different

- **Free and self-hostable** — communities protect their own long tail without
  depending on a hosted service or sending data anywhere.
- **Privacy-respecting by design** — reads **public DNS only**. No scanning of
  anyone's systems, no credentials, no data collection.
- **Remediation-first** — it doesn't just say "you failed DMARC"; it names the
  exact record to publish, the step where most tools stop.
- **Continuous** — it snapshots posture and flags the moment a domain regresses,
  not just a one-shot report.

## What it checks

| Control | What it protects |
|---|---|
| **SPF** | Who is allowed to send mail as the domain (`-all` = enforced) |
| **DMARC** | What receivers do with forged mail (`p=reject` = blocked) |
| **DKIM** | Cryptographic signing so mail can be verified |
| **DNSSEC** | DNS answers are signed and tamper-evident |
| **MTA-STS** | Inbound mail is required to use TLS |
| **MX** | Mail routing is configured |

Each domain gets an **A–D grade**; a domain that grades C or D is spoofable.

## Using it (today's prototype)

Runs on Python with no dependency beyond the standard library + PyYAML; all
network reads go through one gated, honest-User-Agent socket.

```bash
# One domain — full graded report with plain-English fixes
python3 -m foundation.operator_cli security-report --domain acme.com

# Many domains at once — ranked by how spoofable they are (batch/community mode)
python3 -m foundation.operator_cli leads --from-csv businesses.csv --limit 50

# Continuous monitoring — flags any REGRESSION since the last check
python3 -m foundation.operator_cli spoofguard-monitor --domain acme.com

# Remediation — the EXACT DNS records to publish to stop spoofing, safely
python3 -m foundation.operator_cli remediate --domain acme.com
```

The remediation generator is deliberately conservative — it detects the mail
provider from MX and produces SPF at **softfail (~all), never hardfail (-all)**,
DMARC **staged from p=none, never a jump to p=reject**, and DKIM as a provider
instruction (keys are provider-generated, never fabricated). An unrecognised
provider yields a clearly-marked template, never an invented sender — because a
wrong record breaks a business's real mail.

The monitor stores a snapshot each run (`~/.titanos_spoofguard.jsonl` by
default) and, on the next run, reports only what genuinely changed — a
first-ever check has nothing to compare against and honestly reports no change,
never a fabricated one.

## How it works

`gated public-DNS fetch (DNS-over-HTTPS) → parse each control → grade →
remediation → optional snapshot + diff`. It never opens an unsanctioned socket,
never spoofs a User-Agent, and treats an unpublished record as UNKNOWN, never as
"secure by default."

Core modules:
- `foundation/email_security_report.py` — the per-domain posture assessment + grade + fixes.
- `foundation/spoofguard_monitor.py` — snapshot, diff, regression detection, JSONL store.
- `foundation/lead_source.py` + `lead_engine.py` — batch triage across a domain list.

## Honest status

**Prototype, working.** The checks, grading, remediation guidance, batch mode
and monitoring above all run today and are covered by an automated test suite.

**Roadmap (what the grant funds):** a self-host container + setup docs, scheduled
monitoring with alerting, and a community/CERT batch mode with reporting — so
any group can measurably shrink the number of spoofable domains in its own
long tail. All outputs released as free/open source.

## Scope and honesty

SpoofGuard is an **email-security posture check, not a full security audit or
penetration test.** It reflects a domain's public DNS at the time of the check.
It reads only public records and makes no contact with anyone's systems.
