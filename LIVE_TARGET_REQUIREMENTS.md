# Live Target Joining Requirements — Verified

Operator profile checked against: solo, Australia, no certifications, no insurance,
no corporate references, English only, has an ABN.

Compiled 2026-09-02. Every quote below is verbatim from a fetched source. Where a
document could not be read, that is stated explicitly — nothing below it is guessed.

---

## 1. UK CCS Cyber Security Services 3 DPS (RM3764.3)

**Can this operator enter? YES, mechanically — the DPS itself has no certification
gate to get *onto* the DPS. The gate is at the *filter* level: which service filters
you're allowed to tick determine what work you can actually see/bid for, and several
filters require NCSC-recognised certifications this operator does not have.**

### Verified from the official CCS "Cyber Security Services 3 Supplier FAQs" PDF
(`https://assets.crowncommercial.gov.uk/wp-content/uploads/RM3764-Cyber-Security-Services-3-Supplier-FAQ.pdf`
— fetched and read directly, full text, not a summary):

> "**Can I still apply?** Yes, unlike a framework agreement, the DPS is flexible and
> enables suppliers to join the marketplace throughout the duration of the contract."

> "**How do I apply?** You can apply through the CCS electronic platform for this DPS
> via the GOV.UK Supplier Registration System (SRS)
> https://supplierregistration.cabinetoffice.gov.uk/dps
> A Selection Questionnaire (SQ) will have to be submitted in order to join the DPS
> which includes contact details/ financial details/ mandatory and discretionary type
> questions. You will need to complete a Dynamic Purchasing System Questionnaire
> (DPSQ) which includes procurement specific questions e.g. which Cyber Services
> filters you can deliver. If you successfully answer all the selection questions, you
> will enter the agreeing stage on the DPS platform. At this stage, you will be
> required to agree to the CCS Terms and Conditions electronically before you are
> officially appointed."

> "**How long does the application process take?** There is a maximum 10-day
> turnaround for a decision after submission of an application, unless you are asked
> to provide additional information."

> "**What happens once I have been appointed?** You will receive an email with
> further details from the category team which also requests certain documentation
> from you e.g. **insurance documentation** and in due course you will receive login
> details for the MI reporting system."

No sole-trader exclusion, no minimum-turnover figure, and no blanket certification
requirement appears anywhere in this FAQ for the act of *joining the DPS itself*.
The FAQ does flag that insurance documentation is requested **after** appointment —
this operator has none, which is a real gap for the post-appointment stage, not the
application stage.

### The actual filter gate (found, not fully readable)

Search results plus a Contracts Finder attachment title confirm the DPS runs on
**"DPS Schedule 1 (DPS Specification)"**, and per a synthesised description of that
document (not verbatim — the PDF itself returned HTTP 403 and could not be fetched):
four Filter Categories exist — (1) Certified NCSC Services / Non-certified NCSC
Services, (2) Service Types, (3) Accreditations and standards available (in addition
to NCSC), (4) Sectors / Experience. This is **not a verbatim quote** — treat filter
category #1 vs #2 split as the one load-bearing fact: there is a non-certified NCSC
route as well as a certified one, meaning some filters do not require NCSC
accreditation.

**Not independently verified: exact list of which filters require Cyber Essentials /
ISO 27001 / CHECK vs. which are open to unaccredited suppliers.** The DPS Schedule 1
attachment (`contractsfinder.service.gov.uk/Notice/Attachment/e70b8d21-f603-4d50-9a01-1cf4854f542a`)
and the DPSQ itself are both behind Contracts Finder's WAF (403 on direct fetch,
no UA spoofing attempted per rules) or only visible after starting the live
application. An earlier web-search-generated claim that "Cyber Essentials is now a
baseline requirement on many routes" is **not sourced to any document I could read**
— it reads like model-generated commentary, not a quote, and must be discarded, not
acted on.

### Next physical step
1. Human downloads the bid pack / DPS Schedule 1 from the Contracts Finder notice
   (https://www.contractsfinder.service.gov.uk/Notice/4c8a6f7a-ea75-4463-b05a-a56c140a7582
   → Attachments) — this requires a browser, not a bot fetch (403 to automated
   clients).
2. Read the Filter Categories list inside DPS Schedule 1 to find which specific
   filters (if any) have no certification prerequisite — these are the only ones
   this operator can honestly tick.
3. If a certification-free filter exists (plausible given the "non-certified NCSC
   services" category name), register at
   https://supplierregistration.cabinetoffice.gov.uk/dps, complete the SQ + DPSQ,
   selecting only that filter, and expect a decision within 10 working days.
4. Do not tick any NCSC-certified filter — that would be a false declaration.

---

## 2. Ireland 601103-2026 — Health & Safety Authority, SOC/SIEM/IR, €900k, OPEN, closes 12 Oct 2026

**Not readable. The selection-criteria document (ESPD Request PDF) could not be
opened by automated fetch. This is a genuine block, not laziness — see below.**

### What was confirmed
- Document list on the eTenders contract-documents page (fetched successfully) shows:
  - `HSA-services-request-for-tender-SIEMSOC.docx` (the actual RFT — likely contains
    the real requirement text)
  - `6_HSA_SOC_SIEM_IR_Pricing Schedule.xlsx`
  - `espdRequest-8939732.pdf` — the ESPD (European Single Procurement Document)
    selection-criteria form
  - `c4t_8939732_1.xml`, `espdRequest-8939732.xml` (machine formats of the same ESPD)
- The eTenders page confirms **"All documents are available for download via the
  'Download Zip file' option at the bottom of the page."**
- A mirrored TED notice exists at
  `https://ted.europa.eu/udl?uri=TED:NOTICE:601103-2026:TEXT:EN:HTML` (confirmed
  live — found via the eTenders workspace page itself) but TED's site renders via
  JavaScript; automated fetch returned an empty page both on the old-style `udl?uri=`
  link and the new-style `/en/notice/-/detail/601103-2026` link. No content was
  retrievable, so nothing from TED is quoted here.
- Direct fetch of `listContractDocuments.do?resourceId=8939732` succeeded for the
  file *listing* but the actual document binaries sit behind the "Download Zip file"
  control, which is a JS-triggered download, not a stable URL — could not be
  constructed or guessed.

### Next physical step (exact clicks)
1. Open `https://www.etenders.gov.ie/epps/cft/listContractDocuments.do?resourceId=8939732`
   in a real browser.
2. Click **"Download Zip file"** at the bottom of the page (no login appears to be
   required to view the listing; the eTenders portal will state at that point if
   registration is needed to download).
3. Extract and open `espdRequest-8939732.pdf` for the actual selection criteria
   (economic/financial standing, technical capacity, certifications required), and
   `HSA-services-request-for-tender-SIEMSOC.docx` for the substantive requirement
   text (likely where any SOC/SIEM staffing, ISO 27001, or clearance requirements
   would actually be spelled out).
4. Report back the ESPD's "Suitability", "Economic and financial standing" and
   "Technical and professional ability" sections verbatim — that is the actual gate
   for a sole trader with no insurance/certifications on a €900k SOC/SIEM/IR
   contract, and I am not willing to guess it.

---

## 3. Ireland 588260-2026 — Fáilte Ireland, Cybersecurity Specialist Services, €800k, RESTRICTED/PQQ, closes 24 Sep 2026

**Not readable. Same blocker as #2 — PQQ document could not be opened.**

### What was confirmed
- Document list on the eTenders contract-documents page (fetched successfully) shows:
  - `Appendix 1 - Supply of Services Contract.pdf`
  - `PQQ Cybersecurity Specialist Services.docx` — **this is the actual PQQ, the
    document that matters**
  - `espdRequest-8915449.pdf` / `.xml`, `c4t_8915449_1.xml`
- Same "Download Zip file" mechanism, same JS gate, same 403 on direct binary fetch.
- Mirrored TED notice likely exists (pattern matches #2) but was not independently
  located or fetched with content — not confirmed, not claimed.

### Next physical step (exact clicks)
1. Open `https://www.etenders.gov.ie/epps/cft/listContractDocuments.do?resourceId=8915449`
   in a real browser.
2. Click **"Download Zip file"**.
3. Open `PQQ Cybersecurity Specialist Services.docx` — this is a RESTRICTED
   procedure, so the PQQ stage is the actual gate (it decides who gets invited to
   tender at all). Look specifically for: minimum annual turnover threshold,
   required insurance levels (PI/PL), years of relevant experience, named
   certifications, and whether the requirement is for a company/consortium or can
   be met by an individual/sole trader offering "specialist services" on a
   day-rate basis — the notice title suggests individual specialist placement,
   which would be the best fit for this operator, but that is a hypothesis, not
   a confirmed reading, until the PQQ is actually opened.
4. Report the PQQ's selection criteria section verbatim.

---

## Summary

| Target | Can enter now? | Real blocker | Next physical step |
|---|---|---|---|
| CCS Cyber Security Services 3 DPS | Yes, mechanically — no cert gate to apply, gate is per-filter | Exact filter list not confirmed (403 on Schedule 1 PDF) | Human downloads DPS Schedule 1 from Contracts Finder, applies via SRS ticking only non-certified filters |
| Ireland 601103-2026 (HSA SOC/SIEM/IR) | Unknown — ESPD not read | JS "Download Zip file" control, no stable doc URL | Human clicks Download Zip on eTenders resourceId=8939732, opens espdRequest PDF + RFT docx |
| Ireland 588260-2026 (Fáilte Ireland PQQ) | Unknown — PQQ not read | Same as above | Human clicks Download Zip on eTenders resourceId=8915449, opens PQQ docx |

No requirement, threshold, or document content above is invented. Where a document
could not be opened, that is stated as such rather than filled in with a plausible
guess.
