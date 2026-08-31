# Acknowledgements

*A statement by the owner of this repository, Kyle Graham.*

---

## To Anthropic and to OpenAI

TITANOS was built by one person working with frontier language models as the
engineering instrument. I want that stated plainly at the front of the
repository rather than buried, because it is the honest description of how
this work happened.

Claude (Anthropic) did the overwhelming majority of the construction in this
repository — architecture, implementation, adversarial review, and the
self-correction that this project's whole doctrine is built around. Earlier
GPT models (OpenAI) shaped the doctrine, the operating framework, and much of
the thinking that became the constitution these files enforce.

What I am grateful for is specific, and it is not the code volume. It is that
these systems were willing to **find and report their own defects.** Nine
times in this project, the model that had built an instrument turned around
and demonstrated that the instrument was lying — including in cases where the
simpler path was to declare success and move on. Defect #4 in `CASE_STUDY.md`
is the clearest example: a security gate that a model had built, tested and
documented was later shown by that same lineage of models to have never been
connected to anything, with the documentation itself named as the reason
nobody noticed.

That behaviour is the entire reason this repository is worth anything. An
engineering partner that only ever agrees with you produces confident
garbage. The doctrine in these files — *prove before claim, refusal is a
success state, absence of evidence is not evidence of absence* — was not
something I imposed on the tools. It is substantially what emerged from
working with them seriously and watching what actually held up under test.

## No relationship is claimed

To be unambiguous, because this repository's own rules forbid implying
otherwise:

- **No partnership, sponsorship, endorsement, affiliation, or commercial
  relationship exists** between TITANOS and Anthropic, or between TITANOS and
  OpenAI.
- Neither organisation has reviewed, approved, or validated this work.
- Their names appear here only as the makers of tools I used and am thanking.
  Nothing in this repository should be read as a claim of association.

## An open offer

If anyone at either organisation finds this work or the underlying approach
useful, the offer is genuine and open: **I will contribute engineering time
to it.**

Specifically, what has been built here and is transferable:

- **Adversarial self-verification as a build discipline** — every capability
  attacked by mutation before it is trusted, with the negative results kept.
- **A vocabulary that refuses to collapse distinctions** — modelled vs
  observed vs verified vs realized value; signal vs prospect vs qualified vs
  contract; unknown as a first-class state that is never silently zero.
- **Documentation-as-security-control** — the finding that a stale document
  asserting an absence becomes active camouflage for the gap it denies, and
  the checks that now catch it.
- **Agent-swarm engineering with enforced write scopes** — including the
  incident where a subagent's prompt-level scope proved not to be a boundary
  at all and destroyed a thousand lines of concurrent work, which is recorded
  rather than hidden.

Contact is in `README.md` and at `titanos.tech`.

## To anyone reading this repository

The most useful thing here is not the code. It is the honest record of nine
instruments that were wrong, how each one was caught, and what was changed so
that class of error gets caught next time. That record is in `CASE_STUDY.md`,
`failures/FAILURE_ARCHIVE.md`, `INTUITION.md`, and `HUMAN_DECISIONS.md`.

Take any of it. It is MIT licensed. If it saves you from believing one thing
your own system told you that was not true, it did its job.

— Kyle Graham
