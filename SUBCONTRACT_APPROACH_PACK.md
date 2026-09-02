# SUBCONTRACT APPROACH PACK

Built 2026-09-02. Extends `SUBCONTRACT_TARGETS.md` and
`SUBCONTRACT_TARGETS_ENGLISH.md` — does not edit either file. This file
does two things: (1) re-verifies the five established leads named for
this task are still live, quoted and dated; (2) adds newly-checked
firms with a visible individual-contractor entry path; (3) drafts the
approach material itself, so the operator's only remaining step is to
personalise and press send.

**Research-only.** No contact was made, no account created, no form
submitted, no portal signed up to. Every row below traces to a page
this session actually fetched via `WebFetch` — none is inferred,
remembered from training data, or carried over unverified from the two
source files. No personal name, personal email, or personal phone
number appears anywhere in this file; every contact point is a
company-operated inbox or a company's own public page.

**A note on method.** This session's web-search budget was exhausted
before this task began (0 of 200 remaining) — every finding below came
from direct `WebFetch` of a specific URL, not from search. New leads
were sourced from a maintained public GitHub list of Australian/NZ
infosec firms already cited in `SUBCONTRACT_TARGETS_ENGLISH.md`
(`0x10f2c/Aus-Infosec-and-Pentesting-Companies`) plus direct knowledge
of named UK boutique pentest firms, each one individually fetched and
verified rather than assumed live. This is a narrower discovery method
than the two source files used (no fresh web search), stated honestly
rather than hidden — it constrains how many firms could be surveyed in
one pass, not the accuracy of what's reported below.

---

## PART 1 — VERIFICATION OF THE FIVE ESTABLISHED LEADS

Each fetched directly this session (2026-09-02). Quotes are verbatim
from the fetched page content.

### 1. Pulse Security (NZ) — LIVE, confirmed as described

URL: https://pulsesecurity.co.nz/careers — fetched successfully.

Quote: *"email us at careers at pulsesecurity.co.nz with a bit about
yourself, something concrete you can show us that you've broken or
built, what you want to do with your career, and probably a CV or
something."*

**State: unchanged from the base file's finding.** No CV gate (CV is
"probably... or something," not a hard requirement), no certification
mentioned, demonstrated work substitutes for credentials. Still the
lowest-friction entry path found across both source files and this one.

### 2. Volkis (AU, Sydney) — CANNOT BE RE-VERIFIED, same block as before

URLs tried: https://www.volkis.com.au/careers and
https://www.volkis.com.au (root) — both returned **HTTP 403 Forbidden**
to this session's fetch tool.

**State: identical to `SUBCONTRACT_TARGETS_ENGLISH.md`'s prior finding**
(also a 403 on the careers page). The site actively blocks this
fetching method on every path tried, not just `/careers`. This is not
new evidence the associate program still exists or has ended — it is
the same unresolved block, now confirmed on two separate URLs across
two sessions. The only prior evidence for the associate program remains
a third-party staff bio, not Volkis's own site. **Recommend the
operator open volkis.com.au in an ordinary browser directly** (a human
browser is not blocked the way this fetch tool is) before relying on
this lead.

### 3. INFODAS GmbH (Germany) — LIVE, partially confirmed

URL: https://www.infodas.com/en/career/ — fetched successfully.

Quote (Security Testing track): *"You test our customers'
cybersecurity. With or without a hoodie in the Matrix – you decide for
yourself."*

The dedicated vacancies sub-page (https://www.infodas.com/en/career/
vacancies/) was also fetched but returned **no specific job listings in
the fetched content** — the page exists and loads, but this session
could not confirm what, if anything, is currently posted under it. The
"Security Testing" track description on the main careers page is
real and current; whether an open req exists under it right now is
**unconfirmed**, not disproven.

### 4. AWARE7 GmbH (Germany) — LIVE, confirmed, note the URL redirects

URL: https://aware7.com/career/ **redirects (301)** to
https://a7.de/career/ — the company appears to have consolidated onto
its `.de` domain. The `a7.de/karriere` URL cited in the base file also
resolves to the same content.

Quote (initiative applications): *"Wir freuen uns jederzeit über
Initiativbewerbungen - besonders von erfahrenen Pentestern,
Incident-Response-Spezialisten und DevSecOps-Profis."* ("We welcome
unsolicited applications at any time — especially from experienced
pentesters, incident response specialists and DevSecOps professionals.")

Quote (certification funding): *"OSCP, ISO 27001 Lead Auditor, CISM,
CEH - wir übernehmen Kursgebühren, Prüfungskosten und Trainingszeit."*
("We cover course fees, exam costs and training time" for these
certifications.)

**State: unchanged from the base file's finding**, confirmed live
today. Certifications are funded, not gated — the strongest single
signal in either source file that lack of a certification is not
disqualifying here. Use `a7.de/career/`, not the `.com` URL, going
forward.

### 5. OnSecurity (UK) — LIVE, confirmed "not currently recruiting," Associate Network NOT visible on this page

URL: https://onsecurity.io/about-onsecurity/careers/ — fetched
successfully.

Quote: *"We are not currently recruiting. However, if you believe you
would be a good fit to join OnSecurity, please send your CV to
[address given on page]."*

**Correction to the base file's characterisation**: this session's
fetch of OnSecurity's own current careers page found **no mention of an
"Associate Network"** anywhere in the fetched content, and **no
certification requirement stated on this specific page** (the
OSCP/OSWE/CREST requirement the base file found came from a
third-party job aggregator, not this page). This is consistent with,
not contradictory to, the base file's own caveat that the associate
posting "is not confirmed still open on OnSecurity's own site." As of
today: the company is honest that it isn't recruiting, and the
associate-network posting that carried the hard certification bar
cannot currently be found on the company's own site at all — meaning
the entry path may be **less blocked** than the base file assumed
(no visible cert gate on the live page), but also **less concrete**
(no live posting to respond to, only a general CV inbox).

---

## PART 2 — NEW FIRMS WITH A VISIBLE INDIVIDUAL-CONTRACTOR ENTRY PATH

All ten below were individually fetched this session (2026-09-02).
Company size is stated only where the fetched page disclosed it —
otherwise marked "not stated." All are small/boutique consultancies
where a solo contractor relationship is structurally plausible, per the
task's own 5–60-staff heuristic.

| Company | Country | What they do | Entry path (fetched) | Certification bar | Fit note |
|---|---|---|---|---|---|
| **RightSec** | AU | Security consultancy (analyst/engineer/architect/forensics roles) | [rightsec.com.au/career](https://rightsec.com.au/career/) — contact form, "Start your career at RightSec" | Not stated on this page | General entry form, no cert gate found |
| **Secolve** | AU | OT/critical-infrastructure cyber security specialist | [secolve.com/ot-careers](https://secolve.com/ot-careers/) — "Don't see a role that fits? Send us your CV with a cover letter" | Not stated | Explicit invite for unsolicited CVs even with no matching open role |
| **Vertex Cyber Security** | AU | Pentest/security consultancy | [vertexcybersecurity.com.au/careers](https://www.vertexcybersecurity.com.au/careers/) — lists "Junior Penetration Tester" and "Cyber Security Graduate," states *"Whilst not actively hiring, we are open to expressions of interest"* | **None stated** — page explicitly values "passion... demonstrated in their own personal approach" over credentials | Strongest AU no-cert lead found this session besides Airglow; note the page's CV-submission link appeared broken/incomplete in the fetched content — verify manually before relying on it |
| **Sentaris** | AU | Pentest consultancy, two active teams | [sentaris.com.au/careers](https://www.sentaris.com.au/careers/) — **live open roles**: "Penetration Tester (Team Bravo)" wants "testing for at least a year," "Senior Penetration Tester (Team Alpha)" wants 3+ years | Not stated — experience-based, not cert-based | Genuinely open reqs today, lowest experience bar (1+ year) of any live AU posting found |
| **Airglow Security** | AU | Pentest/security services | [airglowsecurity.com.au](https://airglowsecurity.com.au) (careers section on main site) — *"If you're just starting out, show us your passion with challenges or projects you've tried or completed such as from HTB, pentesterlab, etc."* | **None stated** — explicitly substitutes demonstrated capability (HackTheBox/PentesterLab work) for credentials | The closest AU equivalent to Pulse Security's model found this session — built for exactly this operator's profile |
| **Skylight Cyber** | AU | Security research/consultancy | [skylightcyber.com/careers](https://skylightcyber.com/) — *"Send us an Expression of Interest to careers@skylightcyber.com"* | Not stated | Low-friction EOI route, no specific role required to exist first |
| **Security Centric** | AU | Cyber security professional services, Sydney | [securitycentric.com.au/careers](https://www.securitycentric.com.au/careers) — listings found dated **December 2022** | Not stated | **Flag: listings appear stale (3+ years old as fetched)** — page loads and is reachable, but treat the specific postings as unreliable; a fresh general enquiry may still reach someone |
| **The Missing Link (TML)** | AU | Managed security services / consultancy, Melbourne | [themissinglink.com.au/careers](https://www.themissinglink.com.au/careers) — *"Please select one of the below listed positions or email careers@themissinglink.com.au"* | Not stated | General inbox route when no listed role matches |
| **MDSec** | UK | Red team / offensive security research boutique | [mdsec.co.uk/careers](https://www.mdsec.co.uk/careers/) — "Application Security Consultant" and "Security Consultant," applied via Indeed | **Not cert-gated, but skill-gated high** — page asks for "evidence of public-domain exploitation in the form of public advisories," AV-bypass/exploit-dev experience | Real boutique (known for offensive-security research), but the stated bar is advanced original research, not a beginner-friendly entry — only approach if genuinely able to point to that kind of published work |
| **Pentest People (now "WorkNest Secure")** | UK | Penetration testing — merged with Bulletproof in 2025 | [securecareers.worknest.com](http://securecareers.worknest.com/) — "Junior Offensive Security Consultant" (Leeds, onsite) and "Penetration Tester" (Remote, UK); *"If you're passionate, eager to learn, and believe you can bring something to the team, we want to hear from you. We value potential just as much as experience"* | **None stated on the listing** | Live UK reqs, explicit potential-over-experience framing, a remote UK role — worth checking before assuming OnSecurity-style cert gates are standard in the UK market |

### Checked, no usable entry path found (recorded for honesty, not counted above)

- **Elttam** (AU) — no careers content anywhere in the fetched homepage or `/careers/` (404).
- **Red Cursor** (AU) — no careers content found on homepage; no dedicated page found.
- **Cyber Partners** (AU) — no careers content found.
- **Mercury Infosec** (AU) — no careers content found.
- **Silent Grid** (AU) — footer "Jobs" link is a dead `#` placeholder; only a general contact email/phone exists.
- **Content Security** (AU) — no careers content in fetched homepage.
- **Intalock** (AU) — the domain now 301-redirects to InfoTrust (acquired/merged); InfoTrust is a larger MSSP, not sized for a solo-contractor fit, not pursued further.
- **StickmanCyber** — real careers page with a live "Offensive Security Consultant" listing, but **every current role is based in India/Nepal, remote** — not a realistic fit for an AU/NZ/UK-based operator, so not counted as a target above despite the page being genuinely live.
- **Bastion Security Group** (NZ, ZX Security's parent, also absorbed Quantum Security Services via a confirmed 301 redirect) — `/careers` returned 404; ZX Security's own page (already in `SUBCONTRACT_TARGETS_ENGLISH.md`) remains the working entry point, and its "must be currently in New Zealand" restriction still applies.
- **ECSC** (UK) — `/careers` redirects to `wavenet.co.uk`; ECSC has been absorbed into Wavenet, a larger group. Not pursued as a boutique-fit candidate.

---

## PART 3 — DRAFT APPROACH MATERIAL

**Every message below is a DRAFT. The operator must review, personally
edit every placeholder, and send it himself — nothing here is
pre-filled with invented credentials, invented clients, invented
projects, or an invented years-of-experience figure.** Where a genuine
personal fact belongs, a bracketed placeholder marks exactly what to
fill in.

### 3a. Core introduction message (under 150 words)

Use this as the base. Trim or extend per the variant notes in 3b.

> **DRAFT — OPERATOR MUST REVIEW, EDIT AND SEND PERSONALLY**
>
> Subject: Contract / associate testing capacity — [YOUR NAME]
>
> Hi [team / name if known],
>
> I'm reaching out to ask whether you take on contract or associate
> testers for overflow capacity. I don't hold a formal certification
> yet, so I'd rather show you what I can actually do than ask you to
> take my word for it: [YOUR RELEVANT EXPERIENCE — FILL IN, e.g. a
> writeup, a CTF/HTB/PentesterLab profile, a disclosed finding, a
> personal project — link to something concrete and verifiable].
>
> I'm based in [YOUR LOCATION], available for [remote / on-site /
> hybrid — FILL IN], and looking for [contract engagements / an
> associate arrangement / occasional overflow work — FILL IN].
>
> Happy to do a paid trial task or a short scoped piece of work first
> if that's an easier way to evaluate fit than a CV.
>
> [YOUR NAME]
> [YOUR CONTACT DETAILS]

### 3b. Variants by context

**Variant A — firm with an open associate network (e.g. OnSecurity's
Associate Network, if reopened; Volkis's historical program)**

> **DRAFT — OPERATOR MUST REVIEW, EDIT AND SEND PERSONALLY**
>
> Subject: Associate network application — [YOUR NAME]
>
> Hi [team],
>
> I saw you run an associate network for testers and wanted to ask
> about the entry criteria directly, since I don't hold [OSCP/OSWE/
> CREST/etc. — name whichever cert the specific posting names] yet.
> Rather than assume that rules me out, I wanted to show you what I can
> do: [YOUR RELEVANT EXPERIENCE — FILL IN].
>
> If the network specifically requires that certification with no
> exceptions, I understand — but if there's any route in based on
> demonstrated capability instead, I'd like to be considered.
>
> [YOUR NAME] · [YOUR CONTACT DETAILS]

**Variant B — firm with no visible route (general enquiry / info@ only)**

> **DRAFT — OPERATOR MUST REVIEW, EDIT AND SEND PERSONALLY**
>
> Subject: Independent tester — enquiry about contract capacity
>
> Hi,
>
> I couldn't find a careers or associate page, so I'm sending this to
> your general enquiries address. I'm an independent security tester
> (no formal certifications yet) and wanted to ask whether you ever
> bring in outside contractors for overflow work, specific engagements,
> or short-notice capacity.
>
> If useful, here's something concrete I can point to:
> [YOUR RELEVANT EXPERIENCE — FILL IN].
>
> If this isn't something you do, no worries at all — thanks for
> reading this far.
>
> [YOUR NAME] · [YOUR CONTACT DETAILS]

**Variant C — firm advertising a specific open contract/junior role**

> **DRAFT — OPERATOR MUST REVIEW, EDIT AND SEND PERSONALLY**
>
> Subject: Application — [EXACT ROLE TITLE FROM THE POSTING]
>
> Hi [team],
>
> I'm applying for [exact role title]. I don't currently hold
> [certification the posting names, if any], so I want to lead with
> what I can actually demonstrate: [YOUR RELEVANT EXPERIENCE — FILL
> IN].
>
> [ONE SENTENCE ON WHY THIS SPECIFIC ROLE/FIRM — FILL IN, e.g. what
> about their focus area genuinely interests you — do not invent a
> reason].
>
> CV / capability summary attached. Happy to do a practical assessment
> if that's a more useful signal than paper qualifications.
>
> [YOUR NAME] · [YOUR CONTACT DETAILS]

### 3c. Capability summary — attachable, one page

> **DRAFT — OPERATOR MUST REVIEW, EDIT AND SEND PERSONALLY**
>
> ## [YOUR NAME] — Security Testing Capability Summary
>
> **Status:** Independent / no formal certification currently held.
>
> **What I can demonstrate:**
> [YOUR RELEVANT EXPERIENCE — FILL IN. List specific, verifiable items
> only — e.g. named HTB/PentesterLab/TryHackMe rank or completed paths
> with a public profile link, a specific CVE or disclosed finding with
> a reference, a described personal lab/project with what it involved,
> relevant non-security technical background if genuinely applicable.
> Do not list a client, employer, project, or years-of-experience
> figure unless it is true and you can name it specifically.]
>
> **Areas of interest:** [YOUR ACTUAL AREAS — FILL IN, e.g. web
> application testing, infrastructure/network testing, cloud
> configuration review — list only what you can genuinely discuss in
> depth if asked]
>
> **Availability:** [FILL IN — remote/on-site, hours, notice period]
>
> **What I'm asking for:** contract or associate testing work,
> including short scoped engagements or a paid trial task, as a route
> to build a verifiable track record.
>
> **Contact:** [YOUR CONTACT DETAILS]

---

## LIMITATIONS (stated honestly, not hidden)

- This session's web-search budget was fully exhausted before this
  task started — every finding above came from direct URL fetches, not
  search. A fresh session with search budget available would likely
  surface additional UK/AU/NZ firms this pass could not reach (no way
  to discover careers pages for firms whose URL wasn't already known or
  listed in the one GitHub aggregator used).
- Volkis could not be re-verified — both its careers page and its
  homepage returned HTTP 403 to this session's fetch tool, on two
  separate URLs. This is the same block the English-language source
  file already reported, not new information either confirming or
  disproving the associate program still exists.
- INFODAS's specific open-vacancy list could not be confirmed — the
  careers page and its "Security Testing" description are real and
  live, but the dedicated vacancies sub-page returned no listings in
  the fetched content.
- OnSecurity's own live page shows no Associate Network and no
  certification requirement — this narrows, rather than confirms, the
  base file's characterisation of OnSecurity as cert-gated; the
  cert-gated posting the base file found came from a third-party
  aggregator that could not be re-checked this session.
- Ten new firms are listed with a visible entry path; eleven more were
  checked and found to have no usable entry path, a dead/placeholder
  careers link, or a location mismatch (StickmanCyber's India/Nepal
  roles) — recorded honestly in the "no usable entry path" list rather
  than omitted.
- No firm's certification requirement, size, or entry path was
  inferred from name recognition or general knowledge — every claim
  above traces to a page this session actually fetched today
  (2026-09-02).
- No outreach was sent. No account, portal, or ATS registration was
  created anywhere. This file is drafting and verification only.
