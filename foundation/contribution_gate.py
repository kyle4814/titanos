"""May this brick enter someone else's repository, and by which door?

WHY A NEW GATE, WHEN TWO GATES ALREADY EXIST

`publication_gate.py` governs TitanOS's own private->public boundary:
"may we publish this?" `hells_gate.py` governs artifacts coming INBOUND
into the canonical core: "may this enter?" Neither answers the outbound
question this module owns: *another project's* repository has its own
rules, and the question is whether the mechanism we are about to use is
one that project actually accepts.

The state discipline is reused rather than reinvented: fail closed,
default to the cautious state, and never emit a word that means
"trusted".

THE ARCHITECTURAL CORRECTION THIS ENCODES

An earlier pass made SMTP the default delivery surface because
`email_delivery.py` happened to exist. The presence of a transport module
is not architectural authority. The artifact belongs where the work
already lives -- in the repository whose maintainers already have
notification infrastructure, and where the evidence can be reviewed
against the actual code.

So email is demoted from default to conditional, and the conditions are
enumerated rather than left to judgement.

THE FAILURE THIS MODULE EXISTS TO PREVENT

Using a contribution surface as a sales-delivery bypass. A repository
that accepts pull requests is not thereby consenting to receive
marketing. If the artifact is not a genuine, reviewable contribution on
its own terms, no admissible mechanism exists -- and "we could not find a
door" must never degrade into "so we used a different channel".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "DELIVERY_DECISIONS",
    "PLATFORM_RESULTS",
    "EMAIL_PERMITTED_WHEN",
    "ContributionTarget",
    "AdmissionDecision",
    "admit_contribution",
    "email_is_permitted",
    "render_return_sigil",
]

# What door, if any. WITHHOLD is a success state, not a failure.
DELIVERY_DECISIONS = (
    "ADMIT_PR",
    "ADMIT_ISSUE",
    "ADMIT_PRIVATE_SECURITY_CHANNEL",
    "HUMAN_REVIEW_REQUIRED",
    "WITHHOLD",
)

# What the platform did. Deliberately separate from anything a human did.
PLATFORM_RESULTS = (
    "NOT_ATTEMPTED",
    "WITHHELD",
    "SUBMITTED",
    "ACCEPTED_BY_PLATFORM",
    "PLATFORM_REJECTED",
    "AMBIGUOUS",
)

# Email is not the default surface. These are the only conditions under
# which it becomes available at all.
EMAIL_PERMITTED_WHEN = (
    "EXPLICIT_REQUEST",
    "ACTIVE_PARTNERSHIP",
    "REQUIRED_BY_DISCLOSURE_POLICY",
    "OPERATIONAL_CORRESPONDENCE",
)


@dataclass(frozen=True)
class ContributionTarget:
    """What we actually know about the destination repository.

    Every policy field defaults to the unknown/cautious value. A caller
    that has not looked cannot accidentally present the target as
    permissive by omission.
    """

    repository: str
    is_public: bool = False
    accepts_pull_requests: Optional[bool] = None     # None = unknown
    accepts_issues: Optional[bool] = None
    has_security_policy: bool = False
    security_contact: str = ""                       # from SECURITY.md
    contributing_policy_read: bool = False
    policy_forbids_mechanisms: tuple[str, ...] = ()  # e.g. ("ADMIT_PR",)
    relationship: str = "NONE"                       # NONE | EXPLICIT_REQUEST | ACTIVE_PARTNERSHIP

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise ValueError("a contribution target must name a repository")


@dataclass(frozen=True)
class AdmissionDecision:
    decision: str
    reason: str
    mechanism: Optional[str] = None

    def permits_delivery(self) -> bool:
        return self.decision in ("ADMIT_PR", "ADMIT_ISSUE",
                                 "ADMIT_PRIVATE_SECURITY_CHANNEL")


def admit_contribution(
    target: ContributionTarget,
    *,
    brick_is_qualified: bool,
    security_sensitive: bool,
    adds_reviewable_value: bool = True,
) -> AdmissionDecision:
    """Choose the least-intrusive admissible door, or none.

    Order matters and is not arbitrary:

      1. An unqualified brick has no door at all. A finding that did not
         survive the receipt gates is not made deliverable by the
         existence of an open issue tracker.
      2. Security-sensitive findings never take a public door when a
         private one exists. Publishing an unremediated vulnerability
         into a public issue harms the very people it is addressed to.
      3. Explicit policy prohibitions bind absolutely.
      4. Unknown policy escalates to a human -- it does not default to
         the most convenient mechanism.
    """
    if not brick_is_qualified:
        return AdmissionDecision(
            "WITHHOLD",
            "the brick did not survive the receipt gates; an unqualified "
            "finding has no admissible door")

    if not adds_reviewable_value:
        return AdmissionDecision(
            "WITHHOLD",
            "the artifact would be repository noise rather than a reviewable "
            "contribution; a contribution surface is not a delivery channel")

    if not target.is_public:
        return AdmissionDecision(
            "WITHHOLD",
            f"{target.repository} is not publicly accessible, so no public "
            f"contribution path exists")

    if security_sensitive:
        if target.has_security_policy and target.security_contact.strip():
            return AdmissionDecision(
                "ADMIT_PRIVATE_SECURITY_CHANNEL",
                f"{target.repository} publishes a security policy; a sensitive "
                f"finding takes the private route",
                mechanism=target.security_contact)
        return AdmissionDecision(
            "HUMAN_REVIEW_REQUIRED",
            "the finding is security-sensitive and no private disclosure route "
            "was found; publishing it would expose the people it is meant to "
            "protect")

    if not target.contributing_policy_read:
        return AdmissionDecision(
            "HUMAN_REVIEW_REQUIRED",
            f"contribution guidance for {target.repository} has not been read; "
            f"an unread policy is not a permissive one")

    # Least intrusive first: an issue asks, a pull request presumes.
    if target.accepts_issues and "ADMIT_ISSUE" not in target.policy_forbids_mechanisms:
        return AdmissionDecision(
            "ADMIT_ISSUE",
            f"{target.repository} accepts issues; the least-intrusive "
            f"reviewable door")

    if target.accepts_pull_requests and "ADMIT_PR" not in target.policy_forbids_mechanisms:
        return AdmissionDecision(
            "ADMIT_PR", f"{target.repository} accepts pull requests")

    return AdmissionDecision(
        "WITHHOLD",
        f"no permitted mechanism remains for {target.repository}")


def email_is_permitted(relationship: str, policy_requires_email: bool = False) -> bool:
    """Email is conditional, never the default.

    Returns True only for an enumerated condition. A caller cannot argue
    its way here: "we have their address" is not one of the conditions.
    """
    if policy_requires_email:
        return True
    return (relationship or "").strip().upper() in EMAIL_PERMITTED_WHEN


# The canonical ending. Quiet, self-standing, and it does not hold the
# reader's own evidence hostage.
#
# Deliberately absent: any price, any urgency, any claim that a
# partnership is approved or available to everyone. "Arrangements are
# possible" is an invitation to talk; anything stronger would be a
# promise the system cannot keep.
_RETURN_SIGIL = """
------------------------------------------------------------------------

                              TITANOS

                  THIS ARTIFACT STANDS ON ITS OWN.

         If it saved you time, found something real, or pointed
                     at a better next move - we build more.

              More signal. More investigation. More bricks.

         Want TitanOS on a deeper problem?      titanos.tech
         Prefer to talk like a human?           WhatsApp +61 414 244 544

         If a standard engagement isn't the right fit but there is a
         real opportunity to create value together, talk to us.
         Partnership arrangements are possible.

------------------------------------------------------------------------
"""


def render_return_sigil() -> str:
    """The return surface. Not an offer, and not gated on one.

    This is present regardless of the offer decision, because it makes no
    commercial claim: it names where the door is. The offer gate governs
    whether anything is *sold*; it does not govern whether the reader is
    told who made the artifact.
    """
    return _RETURN_SIGIL
