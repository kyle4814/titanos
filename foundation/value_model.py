"""The weighing scale: economic consequence that cannot be invented.

WHY THIS EXISTS

`receipt.py` refuses to carry a price, because a sensor that can carry a
price can be tuned to justify one. But refusing to model economic
consequence at all is its own failure: an operator who is told "this is a
defect" and nothing else has to invent the number themselves, and they
will invent it generously.

So the money question is answered here, in a module the truth layer does
not import, under one law:

    A FIGURE MAY ONLY BE AS STRONG AS ITS WEAKEST INPUT.

The lie this module exists to make structurally impossible is the
partial-measurement lie:

    "We measured transaction volume (62, from the real record).
     We assumed $400 lost per event.
     Therefore you are losing $24,800."

Three of those lines are honest and the fourth is fabricated, and the
fabrication is invisible because the sentence is arithmetically correct.
`ValueModel.exposure()` refuses to emit that number as MEASURED. If any
factor in the product is NOT_MEASURED, the whole exposure is
NOT_MEASURED and the blocking input is named -- the arithmetic is not
performed at all, because a number that exists is a number that gets
quoted.

WHAT IS DELIBERATELY ABSENT

There is no price, fee, quote, or rate-card field. This module measures
what the DEFECT costs the customer. What TitanOS charges is a different
question owned by the existing entitlement layer, and a module that held
both could quietly let one anchor the other.

RELATIONSHIP TO `foundation/receipt.py`

One-way. `value_model` does not import `receipt`, and `Receipt` does not
know this module exists -- a verdict must be reachable with no economic
input at all. `business_receipt.derive_business_receipt()` is the only
place the two meet, and it may only READ a model, never author one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = [
    "SOURCE_STATES",
    "NOT_MEASURED",
    "ValueIntegrityError",
    "ValueInput",
    "DerivedValue",
    "ValueModel",
]

NOT_MEASURED = "NOT_MEASURED"

# The six states the Architect's order requires be kept distinct. They are
# NOT interchangeable and are never collapsed to a boolean "do we have a
# number".
#
#   NOT_MEASURED       nothing was established. Carries no figure, ever.
#   RANGE_ESTIMATED    our own estimate, honestly expressed as an interval.
#   ESTIMATED          our own point estimate. Weaker than it looks: a
#                      point is a range that has hidden its own width.
#   CUSTOMER_REPORTED  the customer asserted it. Real input, unverified.
#   MEASURED           observed directly in a record we read.
#   VALIDATED_REALIZED observed AFTER remediation, in the world. The only
#                      state that describes value that actually happened.
SOURCE_STATES = (
    NOT_MEASURED,
    "RANGE_ESTIMATED",
    "ESTIMATED",
    "CUSTOMER_REPORTED",
    "MEASURED",
    "VALIDATED_REALIZED",
)

# Strength ordering, weakest first. Used ONLY to compute the weakest
# contributor -- never to "average" or "upgrade" anything.
#
# ESTIMATED and RANGE_ESTIMATED share a rank because they carry the same
# evidential weight (both are ours, neither was observed); they differ in
# shape, not in strength. Ties resolve toward RANGE_ESTIMATED, i.e. toward
# the label that admits its own width.
_RANK = {
    NOT_MEASURED: 0,
    "RANGE_ESTIMATED": 1,
    "ESTIMATED": 1,
    "CUSTOMER_REPORTED": 2,
    "MEASURED": 3,
    "VALIDATED_REALIZED": 4,
}

# States whose figure is our own construction rather than an observation.
# These owe an assumption; observations owe a source instead.
_OUR_OWN = ("ESTIMATED", "RANGE_ESTIMATED")


class ValueIntegrityError(ValueError):
    """A value claim tried to be stronger than its inputs."""


@dataclass(frozen=True)
class ValueInput:
    """One quantity, plus an honest account of where it came from.

    `amount` is the point value, or the LOW end when the state is
    RANGE_ESTIMATED. `amount_high` is only meaningful for a range.
    """

    name: str
    unit: str
    status: str
    amount: Optional[float] = None
    amount_high: Optional[float] = None
    source: str = ""       # what record/report this came from
    assumption: str = ""   # required when the figure is ours, not observed

    def __post_init__(self) -> None:
        if self.status not in SOURCE_STATES:
            raise ValueIntegrityError(
                f"source state {self.status!r} is not one of {SOURCE_STATES}"
            )
        if not self.name.strip():
            raise ValueIntegrityError("a value input must be named")

        # NOT_MEASURED means nothing was established. A figure attached to
        # it is a contradiction that would survive into a quote.
        if self.status == NOT_MEASURED:
            if self.amount is not None or self.amount_high is not None:
                raise ValueIntegrityError(
                    f"input {self.name!r} is {NOT_MEASURED} but carries a figure; "
                    f"an unmeasured quantity has no number, only a gap"
                )
            return

        if self.amount is None:
            raise ValueIntegrityError(
                f"input {self.name!r} claims status {self.status} but carries no "
                f"figure; state {NOT_MEASURED} instead"
            )
        if self.amount < 0 or (self.amount_high is not None and self.amount_high < 0):
            raise ValueIntegrityError(f"input {self.name!r} has a negative magnitude")
        if not self.unit.strip():
            raise ValueIntegrityError(
                f"input {self.name!r} carries a bare figure with no unit; "
                f"a number without a unit cannot be checked"
            )

        if self.status == "RANGE_ESTIMATED":
            if self.amount_high is None:
                raise ValueIntegrityError(
                    f"input {self.name!r} is RANGE_ESTIMATED but has no upper "
                    f"bound; a range with one end is a point estimate in disguise"
                )
            if self.amount_high < self.amount:
                raise ValueIntegrityError(
                    f"input {self.name!r} has an inverted range"
                )
        elif self.amount_high is not None:
            raise ValueIntegrityError(
                f"input {self.name!r} supplies an upper bound but is not "
                f"RANGE_ESTIMATED; say the figure is a range or do not give one"
            )

        # An observation owes a source; a construction owes an assumption.
        if self.status in _OUR_OWN:
            if not self.assumption.strip():
                raise ValueIntegrityError(
                    f"input {self.name!r} is {self.status} -- our own figure -- and "
                    f"must state the assumption it rests on"
                )
        elif not self.source.strip():
            raise ValueIntegrityError(
                f"input {self.name!r} claims {self.status} but names no source; "
                f"an observation must say what was observed"
            )

    def is_range(self) -> bool:
        return self.amount_high is not None

    def render(self) -> str:
        if self.status == NOT_MEASURED:
            return f"{self.name}: NOT MEASURED"
        if self.is_range():
            figure = f"{self.amount:g}-{self.amount_high:g} {self.unit}"
        else:
            figure = f"{self.amount:g} {self.unit}"
        basis = self.source.strip() or self.assumption.strip()
        return f"{self.name}: {figure} [{self.status}: {basis}]"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "status": self.status,
            "amount": self.amount,
            "amount_high": self.amount_high,
            "source": self.source,
            "assumption": self.assumption,
        }


@dataclass(frozen=True)
class DerivedValue:
    """The output of the scale. May legitimately hold no figure at all."""

    status: str
    unit: str
    amount: Optional[float] = None
    amount_high: Optional[float] = None
    blocked_by: tuple[str, ...] = ()   # inputs that stopped the arithmetic
    assumptions: tuple[str, ...] = ()

    def is_measured(self) -> bool:
        return self.status != NOT_MEASURED

    def render(self) -> str:
        """The only sanctioned way to say this out loud.

        Never returns a bare number: the status travels with the figure,
        because a figure quoted without its status is how MEASURED and
        ESTIMATED become the same sentence in a customer's memory.
        """
        if self.status == NOT_MEASURED:
            if self.blocked_by:
                return (
                    "NOT MEASURED (blocked by: " + ", ".join(self.blocked_by) + ")"
                )
            return "NOT MEASURED"
        if self.amount_high is not None:
            figure = f"{self.amount:g}-{self.amount_high:g} {self.unit}"
        else:
            figure = f"{self.amount:g} {self.unit}"
        text = f"{figure} [{self.status}]"
        if self.assumptions:
            text += " under stated assumptions: " + "; ".join(self.assumptions)
        return text

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "unit": self.unit,
            "amount": self.amount,
            "amount_high": self.amount_high,
            "blocked_by": list(self.blocked_by),
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True)
class ValueModel:
    """A named set of inputs plus an explicit, auditable derivation.

    The derivation is deliberately restricted to a PRODUCT of named
    factors. That is not a limitation to be lifted later -- it is the
    reason the output is checkable. A model that could evaluate arbitrary
    expressions would let the derivation itself carry the fabrication,
    somewhere no reviewer would look.
    """

    inputs: tuple[ValueInput, ...] = ()
    # Names of the inputs multiplied together to give the exposure.
    factors: tuple[str, ...] = ()
    result_unit: str = ""
    period: str = ""   # e.g. "per year" -- free text, never computed from

    def __post_init__(self) -> None:
        seen = set()
        for i in self.inputs:
            if i.name in seen:
                raise ValueIntegrityError(f"duplicate value input {i.name!r}")
            seen.add(i.name)
        for f in self.factors:
            if f not in seen:
                raise ValueIntegrityError(
                    f"derivation multiplies {f!r}, which is not an input; a "
                    f"factor that is not declared cannot be reviewed"
                )
        if self.factors and not self.result_unit.strip():
            raise ValueIntegrityError(
                "a derivation that produces a figure must state its result unit"
            )

    def get(self, name: str) -> Optional[ValueInput]:
        for i in self.inputs:
            if i.name == name:
                return i
        return None

    def unmeasured_inputs(self) -> tuple[str, ...]:
        return tuple(i.name for i in self.inputs if i.status == NOT_MEASURED)

    def exposure(self) -> DerivedValue:
        """Multiply the declared factors -- or refuse, and say why.

        THE CENTRAL RULE lives here: if any factor is NOT_MEASURED, the
        product is not computed at all. Not computed-then-flagged, not
        computed-with-a-caveat: not computed. A number that exists in the
        object is a number that ends up in a sentence.
        """
        if not self.factors:
            return DerivedValue(status=NOT_MEASURED, unit=self.result_unit or "")

        chosen = [self.get(f) for f in self.factors]
        blocked = tuple(c.name for c in chosen if c.status == NOT_MEASURED)
        if blocked:
            return DerivedValue(
                status=NOT_MEASURED, unit=self.result_unit, blocked_by=blocked
            )

        low = 1.0
        high = 1.0
        for c in chosen:
            low *= c.amount
            high *= (c.amount_high if c.amount_high is not None else c.amount)

        # The weakest contributor governs the whole. Ties toward the label
        # that admits its own width.
        weakest = min(_RANK[c.status] for c in chosen)
        candidates = {c.status for c in chosen if _RANK[c.status] == weakest}
        if "RANGE_ESTIMATED" in candidates:
            status = "RANGE_ESTIMATED"
        else:
            status = sorted(candidates)[0]

        # A product of an interval is an interval, whatever the labels say.
        if high != low and status != "RANGE_ESTIMATED":
            status = "RANGE_ESTIMATED"

        assumptions = tuple(
            c.assumption.strip() for c in chosen if c.assumption.strip()
        )
        return DerivedValue(
            status=status,
            unit=self.result_unit,
            amount=low,
            amount_high=high if high != low else None,
            assumptions=assumptions,
        )

    def render(self) -> str:
        lines = [f"EXPOSURE: {self.exposure().render()}"]
        if self.period:
            lines[0] += f" {self.period}"
        lines.append("INPUTS:")
        for i in self.inputs:
            lines.append(f"  - {i.render()}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "inputs": [i.to_dict() for i in self.inputs],
            "factors": list(self.factors),
            "result_unit": self.result_unit,
            "period": self.period,
            "exposure": self.exposure().to_dict(),
        }
