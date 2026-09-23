# Verification Portal — Product Direction

## Concept

A user pastes information into a portal: an AI answer, article, claim, message, document excerpt, research statement or other text.

The portal decomposes the input into claims and returns a structured report.

### Candidate result states

- **SUPPORTED** — the claim has sufficient declared evidence for the chosen rule.
- **CONTRADICTED** — available evidence conflicts with the claim.
- **UNSUPPORTED** — a claim was identified but adequate evidence was not found.
- **UNKNOWN** — the available evidence is insufficient to classify the claim.
- **MODELLED** — the statement follows from explicit assumptions or simulation rather than direct observation.
- **REQUIRES HUMAN REVIEW** — the consequence or ambiguity exceeds the automated authority boundary.

These labels are product hypotheses until implemented and validated end-to-end.

## Simulation boundary

The portal should make simulation explicit. A simulation can answer:

> If assumptions A, B and C hold, what follows?

It cannot silently become:

> Therefore A, B and C are true.

For competing simulations, the interface should preserve:

**assumptions → model → outputs → sensitivity → evidence status**

rather than collapsing the output into a single certainty score.

## AI hallucination boundary

The portal should not promise perfect hallucination detection. A useful first milestone is narrower:

1. extract claims;
2. attach sources/evidence where available;
3. detect missing or conflicting support;
4. preserve uncertainty;
5. show the user exactly why a classification was reached;
6. allow correction and re-checking.

## MVP research questions

- How accurately can claims be segmented?
- How often can evidence be matched correctly?
- How should conflicting primary sources be represented?
- What does a useful human review screen look like?
- What latency and cost are acceptable?
- Which domains have sufficiently structured public evidence?
- Which failure modes are more harmful than a false negative?

## Non-goal

The portal is not intended to become an authority that tells users what to believe. Its job is to expose evidence, provenance, uncertainty and disagreement so the user can make the decision.
