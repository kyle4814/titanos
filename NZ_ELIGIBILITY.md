# NZ_ELIGIBILITY.md — can a solo Australian operator bid on NZ GETS security tenders?

**Sweep date:** 2026-09-02, live, via `foundation/mouth_common.py::fetch_feed()`
with fresh `DiscoveryPolicy` objects, no spoofed User-Agent (this fetcher's own
honest identifier: `titanos-cosmic-library-mouth/1`). Robots.txt checked before
any detail-page fetch. Small, polite sample only (3 of 36 candidates, several
seconds apart, one request per page) — this is someone's live public service.

## 1. Robots.txt verdict — FETCHING DETAIL PAGES IS PERMITTED

`https://www.gets.govt.nz/robots.txt`, fetched live, full and complete text:

```
User-agent: SEMrushBot
User-agent: SemrushBot
User-agent: SemrushBot-SA
Disallow: /
```

No general `User-agent: *` block, no disallow on `/*/ExternalTenderDetails.htm`
or any path this fetcher touches. Only three named SEO-crawler bots are
disallowed, site-wide. This fetcher's own honest User-Agent
(`titanos-cosmic-library-mouth/1`) is not one of them, so fetching individual
`ExternalTenderDetails.htm?id=NNNNN` pages — the exact page every RSS
`<item><link>` already points at — is permitted. **Did not stop; proceeded.**

## 2. What the detail page actually carries (sample of 3, live)

Fetched, six seconds apart, one request each:

| Notice | Buyer | URL |
|---|---|---|
| 322859 - Security Services | University of Waikato | `/UW/ExternalTenderDetails.htm?id=34808478` |
| Corporate Security | Ministry of Education | `/MEDU/ExternalTenderDetails.htm?id=34721345` |
| Identity Management Services | Statistics New Zealand | `/SNZ/ExternalTenderDetails.htm?id=34705876` |

Every page carries one HTML table (`tender-details-info-tbl`) with a fixed,
small field set: RFx ID, Tender Name, Reference #, Open Date, Close Date,
Department/Business Unit, Tender Type, Tender Coverage, Categories, Regions,
**Exemption Reason**, **Required Pre-qualifications**, Contact, Alternate
Physical Delivery Address, Alternate Physical Fax Number. That is the entire
field set observed across all three samples — **no line item exists anywhere
on the page for insurance, professional certification, references/track
record, legal form/consortium rules, financial-capacity thresholds, or any
other selection-criterion vocabulary.** Whatever an RFx's own full response
requirements are, they live in a downloadable RFx document this page does not
embed a link to (none was observed on any of the three samples) — not
something this module fetches or claims to have read.

**The one genuinely new, genuinely usable field:** `Required
Pre-qualifications`. Unlike the RSS feed (title/organisation/close-date only,
zero criteria vocabulary — see `foundation/mouth_gets_nz.py`'s own module
docstring and `foundation/sources.py`'s CRITICAL HONESTY RULE), this field is
**positively stated** on the detail page. All three samples carried the
literal value `"None"`:

| Notice | Required Pre-qualifications | Exemption Reason |
|---|---|---|
| University of Waikato — Security Services | **None** | None |
| Ministry of Education — Corporate Security | **None** | None |
| Statistics NZ — Identity Management Services | **None** | None |

A stated `"None"` is real evidence — the agency did not impose a formal
pre-qualification/panel-membership gate for that specific notice. It is
**not** evidence about insurance, certification, references, or financial
capacity, none of which ever appear as a field on this page — those stay
strictly **UNKNOWN**, not "no requirement." This distinction is enforced in
code: `foundation/mouth_gets_nz.py::parse_tender_detail()` extracts only
labels genuinely present in the page's own table; a label the page never
carries is simply absent from the returned dict, never defaulted to "None"
or any other value (`foundation/tests/test_mouth_gets_nz.py::
ParseTenderDetailTests::test_a_field_absent_from_the_page_is_absent_from_the_dict`
pins this directly).

**Honest limits of this finding:**
- Sample size is 3 of 36 security-relevant NZ notices (and 3 of 324 total
  open notices). A different notice could use a different template, or could
  state a real pre-qualification requirement — this was not checked against
  every notice, and this module does not claim it was.
- "Required Pre-qualifications: None" answers only the formal
  panel/pre-qualification question. It says nothing about whether the buyer's
  full RFx document (not fetched) imposes insurance, a minimum trading
  history, a security clearance, or a reference requirement in its own body
  text — those remain genuinely unresolved, not ruled out.
- GETS itself requires a free supplier account to submit a response (a
  platform-level barrier, not a corporate-scale prequalification
  questionnaire) — a known characteristic of the platform, not verified
  per-listing this cycle.

## 3. Can a foreign (Australian) supplier bid on NZ government work? YES — quoted, NZ government source

Fetched live from `https://www.procurement.govt.nz/` (robots.txt permits;
only `/admin/`, `/Security/`, `/server-error/`, `/page-not-found/` are
disallowed). From `/government-procurement-framework/government-procurement-rules/background-to-the-rules/`:

> "New Zealand is committed to open, transparent and competitive government
> procurement that: delivers public value **[and] does not discriminate
> against suppliers (domestic or international)** [and] meets agreed
> international standards. The Rules reflect these values and standards."

> "Access to markets is secured through Free Trade Agreements (FTAs). Under
> FTAs, countries offer reciprocal access to their government contracts and
> agree minimum standards for open, transparent and fair government
> procurement. **The Rules reflect New Zealand's FTA commitments, the
> Australia New Zealand Government Procurement Agreement, and align with the
> World Trade Organization Agreement on Government Procurement (GPA).**"

This confirms the task brief's premise directly, from the New Zealand
Government Procurement rules themselves, not inferred from the general CER/
ANZSCEP/WTO GPA framework: NZ government procurement policy explicitly
commits to non-discrimination against international suppliers, and names the
Australia–New Zealand Government Procurement Agreement by name alongside the
WTO GPA as the instruments the Rules give effect to.

**What this source does NOT say, and what stays UNKNOWN:** no page fetched
in this cycle (`procurement.govt.nz` homepage, the Government Procurement
Rules index, `background-to-the-rules/`, `general-information/`, `suppliers/`)
states or implies a requirement for a New Zealand Business Number (NZBN) or
NZ local presence as a condition of *bidding*. "NZBN"/"business number" does
not occur anywhere in any of the five pages fetched. This is an honest
absence, not a confirmed "no requirement" — a downstream requirement (e.g.
for invoicing, tax withholding, or contract execution once awarded) may exist
elsewhere and was not checked; this cycle only establishes that no bidding-
eligibility rule requiring one was found in the general procurement-policy
pages read.

## 4. The answer to the task's actual question

**Can this operator (a solo, uncertified Australian operator) bid on NZ
government work at all?** Yes, in principle — NZ government procurement
policy explicitly does not discriminate against international suppliers
(quoted above), and the Australia–New Zealand Government Procurement
Agreement specifically covers this pairing. Nothing found this cycle
restricts bidding by nationality or requires a local NZ entity to *submit* a
response through GETS.

**Do any of the 36 live security-relevant NZ matches have no stated barrier
a solo uncertified operator would fail?** For the 3 sampled: **all three
state `Required Pre-qualifications: None`** — a real, positive absence of a
formal pre-qualification gate, not an inferred one. That is the honest
current answer for those 3. It is **not** a claim that all 36 are barrier-
free — the other 33 were not individually checked this cycle (respecting the
politeness constraint on this fetch), and even for the 3 checked,
whatever a downloadable RFx document might additionally require (insurance,
references, security clearance, minimum experience) is genuinely unresolved,
not ruled out.

## 5. What would close the remaining gap

The single highest-leverage next step, if this thread continues: sample a
few more of the 36 (still politely, still several seconds apart) to see
whether `Required Pre-qualifications: None` is the norm or an artifact of
these three buyers specifically — and, separately, check whether any of the
36 links to a downloadable RFx document (none of the three sampled did) that
would carry the finer-grained criteria this page's own table structurally
cannot.
