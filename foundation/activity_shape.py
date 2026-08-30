"""Does repository activity actually differ between targets?

WHY THIS EXISTS

The previous unit proved coverage: a repository-native commit read reached
18 of 18 discovered targets where publication reached 1. But it reduced
every one of those reads to a single bit -- "latest commit is fresh: yes"
-- and every target answered yes. A dimension that agrees about everything
ranks nothing.

The variation was already in the response and was being thrown away. Ten
commits carry their spacing and their authorship, and those differ between
a repository where one person pushed ten times in an hour and one where
four people landed work across a week.

WHAT THIS IS NOT

Not a score. `ActivityShape` reports measured quantities with their units
and refuses to collapse them into one number, because "how recent",
"how sustained" and "how many hands" are three different facts and a
target can be strong in one and empty in the others.

Nothing here decides anything. Whether these facts deserve to enter the
gravity model is a question for evidence, answered by measuring whether
they actually separate targets -- not assumed by wiring them in first.

THE CONFOUNDS, NAMED BEFORE THEY ARE MEASURED

- The discovery population is sorted by recent issue update, so it is
  selected for activity. Variation found here is variation WITHIN an
  already-active set, which is the honest scope of the claim.
- A ten-commit window sees a busy repository over hours and a quiet one
  over years. `span_days` is therefore a property of the window, not of
  the repository's whole life, and is named that way.
- Bots commit. `bot_authors` is counted separately rather than silently
  inflating the number of hands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

__all__ = ["ActivityShape", "shape_of", "UNKNOWN_SHAPE", "BOT_PATTERN"]

# GitHub marks accounts as type "Bot"; many automation accounts do not set
# it, so the name pattern is a second, independent check.
BOT_PATTERN = re.compile(r"(\[bot\]$|^dependabot|^renovate|^github-actions)", re.I)


def _parse(stamp: str) -> Optional[datetime]:
    try:
        d = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class ActivityShape:
    """Three separate measurements over one commit window.

    `observed` is False when the window could not be measured at all --
    which is not the same as a repository with no activity, and never
    reports zeros for the quantities it could not compute.
    """

    observed: bool
    commits: int = 0
    latest_age_days: Optional[float] = None
    span_days: Optional[float] = None
    human_authors: int = 0
    bot_authors: int = 0
    window: int = 0
    note: str = ""

    def hands(self) -> int:
        """Distinct human authors. Bots are excluded rather than counted as
        collaborators, because a repository kept alive by dependabot is not
        a repository with people moving in it."""
        return self.human_authors

    def is_burst(self) -> bool:
        """Many commits compressed into a short window.

        Descriptive only. A burst is not urgency, not demand, and not
        value -- it is a shape, and it is reported as one.
        """
        return (self.observed and self.commits >= 5
                and self.span_days is not None and self.span_days <= 1.0)

    def show_the_measurements(self) -> str:
        if not self.observed:
            return f"ACTIVITY SHAPE unmeasured -- {self.note or 'no reason recorded'}"
        parts = [f"ACTIVITY SHAPE over {self.commits} commit(s) "
                 f"(window {self.window})"]
        parts.append(f"  latest        {self.latest_age_days:.2f} days ago"
                     if self.latest_age_days is not None
                     else "  latest        UNKNOWN")
        parts.append(f"  span          {self.span_days:.2f} days"
                     if self.span_days is not None
                     else "  span          UNKNOWN")
        parts.append(f"  human authors {self.human_authors}")
        parts.append(f"  bot authors   {self.bot_authors}")
        return "\n".join(parts)


UNKNOWN_SHAPE = ActivityShape(observed=False, note="not measured")


def _is_bot(login: str, kind: str) -> bool:
    return kind == "Bot" or bool(BOT_PATTERN.search(login or ""))


def shape_of(items: Sequence[dict], window: int = 0,
             now: Optional[datetime] = None) -> ActivityShape:
    """Measure one commit window. Never invents a zero it did not observe.

    An empty item list yields `observed=False`, not a shape full of zeros:
    the caller already distinguishes "looked and saw nothing" from "never
    looked", and this must not quietly re-merge them by reporting both as
    a repository with no activity.
    """
    items = list(items)
    if not items:
        return ActivityShape(observed=False, window=window,
                             note="no commits in the observed window")

    now = now or datetime.now(timezone.utc)
    times = [t for t in (_parse(i.get("authored_at", "")) for i in items)
             if t is not None]
    ages = sorted((now - t).total_seconds() / 86400.0 for t in times)

    humans, bots = set(), set()
    for i in items:
        login = str(i.get("author_login", ""))
        kind = str(i.get("author_type", ""))
        identity = login or str(i.get("author_email", ""))
        if not identity:
            continue
        (bots if _is_bot(login, kind) else humans).add(identity)

    return ActivityShape(
        observed=True, commits=len(items), window=window or len(items),
        latest_age_days=ages[0] if ages else None,
        span_days=(ages[-1] - ages[0]) if len(ages) >= 2 else None,
        human_authors=len(humans), bot_authors=len(bots),
        note="" if ages else "no parseable commit times in the window")


def spread(shapes: Iterable[ActivityShape], attr: str) -> Optional[float]:
    """How much one measurement actually varies across a population.

    The whole discrimination question in one function: a dimension whose
    spread is zero cannot separate anything, however well it covers.
    """
    vals = [getattr(s, attr) for s in shapes
            if s.observed and getattr(s, attr) is not None]
    return (max(vals) - min(vals)) if len(vals) >= 2 else None
