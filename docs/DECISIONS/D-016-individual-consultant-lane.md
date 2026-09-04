# D-016 — The individual-consultant lane (ADB / UNDP / EU / UNGM / World
# Bank) cannot be verified or swept by an honest automated agent. Every
# source is WAF-blocked, robots-disallowed, or a JS SPA. It is a
# human-browser lane, and that is now recorded so no cycle re-probes it.

STATUS: DECISION RECORDED — NO MODULE BUILT. Resolves a standing
high-potential UNVERIFIED (ADB) and the whole opportunity class behind it.
AGENT: autonomous ops cycle
DATE: 2026-09-03

## THE QUESTION

Development-bank and UN **individual-consultant** modalities are, on
paper, the best structural fit after Synack: they procure from a PERSON,
so there is no company, insurance, turnover or reference requirement —
exactly the walls that ruled out every EU tender. ADB in particular has
sat on the board as **UNVERIFIED** ("the single most important finding if
accurate") because the reported eligibility — "citizen of a member
country, not barred, not a close relative of ADB staff" — could never be
confirmed. This cycle asked whether it can be confirmed from a primary
source, so the lane can be promoted to the roster or closed honestly.

## WHAT WAS TRIED, LIVE, 2026-09-03 (honest UA, robots respected)

| Source | Result | Verdict |
|---|---|---|
| **adb.org** (the static consultant guidelines) | **HTTP 403** to an honest fetcher — even `/robots.txt` 403s | **WAF-blocked** |
| **cms.adb.org** (the CMS application) | JS SPA shell (prior cycles) — routes client-side | **SPA** |
| **procurement-notices.undp.org** | `robots.txt` = **`Disallow: /`** (entire site) | **robots-disallowed** |
| **EU expert portal** (ec.europa.eu funding-tenders) | 200 but a ~60 KB client-rendered shell, no eligibility content server-side | **SPA** |
| **UNGM / World Bank** consultant pages | guessed static paths returned 404; no stable server-rendered eligibility page located | **not reachable statically** |

None was defeated by spoofing or evasion — those are refused. UNDP's page
was retrieved once before its `robots.txt` was read; its CONTENT IS NOT
USED here, only the fact that the site disallows automated access.

## THE DECISION

- **The individual-consultant lane is human-browser-only.** No source in
  it exposes eligibility criteria to an honest automated agent: ADB's
  authoritative site is WAF-blocked, UNDP disallows all crawling, and the
  EU/CMS front-ends are client-rendered.
- **ADB moves from "UNVERIFIED, might be automatable" to "UNVERIFIED,
  human-browser-only — WAF-confirmed."** It stays on the board and in the
  digest as UNVERIFIED (a wrong eligibility claim is the exact error that
  produced a false QUALIFIED on ECHA), and the one action that resolves it
  is unchanged: Kyle opens cms.adb.org in a normal browser and clicks
  Register; the form states what it requires. Ten minutes only he can spend.
- **No sweep to build.** Building a fetcher for any of these would mean
  driving a headless browser or evading a WAF/robots rule — both refused.
- **Recorded so no future cycle re-probes** ADB.org, UNDP, or the EU
  portal expecting a different result.

## WHY THIS MATTERS ANYWAY

The lane is not dead — it is genuinely the best-fit modality for a skilled
solo operator with no credentials, and it is worth Kyle's ten minutes per
source. It simply cannot be worked from here. This is the same shape as
D-015 (bounty platforms): the automated boundary is mapped so effort goes
where it actually pays, and the human-browser tasks are named plainly.
