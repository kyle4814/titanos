"""Make attacker-controlled text safe to DISPLAY, without destroying it.

WHY THIS EXISTS

`mouth_github_issues.py::parse_items` captures issue `title`, `labels`,
`author_login` straight off the public GitHub search API; `mouth_github_
commits.py` captures commit `subject` the same way. Both are attacker-
controlled: anyone can open an issue or push a commit to a public repo.
Those fields flow into `foundation/tentacles.py` and become
`CanonicalSignal.claim` and `evidence`, which `foundation/signal_spine.py::
RawValueMapEntry.render()` turns into report text and `foundation/
opportunity.py` hands to an operator or a future LLM to read. An
exhaustive grep of that path (2026-09-01) found no sanitisation, no
escaping, no length cap, and no control-character stripping anywhere in
it. A commit subject or issue title is exactly as trusted, right now, as
a string this repository generated itself. It should not be.

WHAT THIS MODULE IS NOT

It is not an authority boundary. Nothing here decides whether text may
run, execute, or be trusted -- this repository has no code path that
would let ingested text do any of that today, and if one is ever built,
it needs its own gate, not this module. This module has exactly two
narrow jobs: stop a hostile string from rewriting the terminal/report it
is displayed in, and surface a short list of known social-engineering
phrases as EVIDENCE for a human or caller to weigh -- never a verdict.

THE ONE RULE THAT MATTERS MOST

**The original text must always be preserved verbatim, separately from
anything this module produces for display.** `evidence` in this
repository's signal spine is kept exactly as observed -- that is a
deliberate, load-bearing design choice (see `signal_spine.py`'s own
docstring), and neutralising text for rendering must never become an
excuse to overwrite it. `neutralise()` and `looks_like_injection()` are
both pure functions: they take a string, they return a new value, they
never mutate or discard the caller's original. `UntrustedText` /
`describe()` go one step further and make the safe pattern the easy
pattern: they hand back the original and the rendered form together in
one frozen object, so a caller who reaches for the convenience API
cannot accidentally end up holding only the neutralised copy.

WHAT `looks_like_injection` IS HONEST ABOUT

It is a blocklist. A blocklist catches only what someone already thought
of and phrased the way the list expects. It returns the MARKERS FOUND --
a tuple, never a boolean -- because this repository's discipline (see
`demand_direction.py`, `activity_shape.py`) is that a detector reports
evidence and a caller decides what the evidence means. An empty tuple is
not a clearance; it means no listed phrase matched, nothing more.

UNICODE: HANDLED PARTIALLY, NAMED HONESTLY

Zero-width characters (U+200B ZERO WIDTH SPACE, U+200C, U+200D, U+FEFF)
and the bidi-override family (U+202A-U+202E, U+2066-U+2069) ARE stripped
by `neutralise()` and normalised away before `looks_like_injection()`
matches -- both are single techniques a text field genuinely uses today
to reorder or hide characters in a rendered terminal/report, well within
this module's actual scope. Homoglyph substitution (Cyrillic і for
Latin i, fullwidth forms, etc.) is NOT handled: detecting it reliably
needs a confusables table this module does not carry, and guessing badly
would be worse than saying nothing. Treat `looks_like_injection` finding
no markers in text containing homoglyphs as exactly what it is --
untested, not cleared.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

__all__ = [
    "DEFAULT_MAX_LEN",
    "INJECTION_MARKERS",
    "UntrustedText",
    "neutralise",
    "looks_like_injection",
    "describe",
]

# A cap chosen to keep a single field from dominating a rendered report
# (see the `signal_spine.py::RawValueMapEntry.render()` consumer this
# module was built for) while still showing enough of a title/subject to
# be useful. Callers with a different display budget pass their own.
DEFAULT_MAX_LEN = 300

_TRUNC_TEMPLATE = " …[TRUNCATED, {n} more chars]"

# ANSI/VT100 escape sequences: CSI (`ESC [ ... letter`), OSC (`ESC ] ...
# terminated by BEL or ST`), and the shorter two-character escapes
# (`ESC` followed by a single letter, e.g. `ESC c` = full reset). These
# are the actual mechanism by which a string can rewrite a terminal line
# it is printed into -- cursor moves, colour changes, screen clears.
_ANSI_CSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_ANSI_OSC = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?")
_ANSI_SHORT = re.compile(r"\x1b[@-Z\\-_]")

# C0 controls except \t \n \r (handled separately below), plus DEL and
# the C1 control block. \t is left alone deliberately -- a tab cannot
# forge a line or move the cursor the way a newline or ESC can.
_CONTROL_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x80-\x9f]")

_NEWLINES = re.compile(r"\r\n|\r|\n")

# Zero-width and bidi-override characters: named and handled per the
# module docstring's Unicode section. Format category "Cf" covers both
# families plus a handful of other invisible formatting codepoints;
# filtering by category rather than a hand-typed codepoint list means a
# lookalike Cf codepoint not enumerated here is still caught.
def _strip_invisible_formatting(text: str) -> str:
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def neutralise(text: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Return a DISPLAY-SAFE rendering of `text`. Never mutates `text`.

    Order matters and is deliberate: strip invisible formatting/bidi
    codepoints first (they can hide the very control chars and ANSI
    bytes the later steps look for), then ANSI escapes, then remaining
    control characters, then collapse newlines into a visible, single-
    line marker so one field cannot forge extra lines in a rendered
    report, then cap length with a truncation marker that always states
    how much was cut -- never a silent cut.

    Idempotent: `neutralise(neutralise(text, n), n) == neutralise(text, n)`
    for any `n`, because the output of one pass contains none of the
    control characters, ANSI bytes, invisible formatting codepoints, or
    embedded newlines the passes above remove, and is already within
    the length budget the truncation step enforces.

    Not an authority boundary -- see the module docstring. This function
    only makes `text` safe to print; it does not make it safe to trust.
    """
    if not isinstance(text, str):
        text = str(text)

    s = _strip_invisible_formatting(text)
    s = _ANSI_OSC.sub("", s)
    s = _ANSI_CSI.sub("", s)
    s = _ANSI_SHORT.sub("", s)
    s = _CONTROL_CHARS.sub("", s)
    # Collapse any run of newlines/carriage returns to one literal,
    # visible two-character "\n" -- ASCII, unambiguous, reads on one
    # line. A function replacement is required here: `re.sub` treats a
    # plain string replacement as a template and would decode the
    # literal backslash-n back into an actual newline character,
    # silently reopening the exact hole this line exists to close.
    s = _NEWLINES.sub(lambda _m: "\\n", s)

    if max_len <= 0:
        return ""
    if len(s) <= max_len:
        return s

    removed = len(s) - max_len
    marker = _TRUNC_TEMPLATE.format(n=removed)
    if len(marker) >= max_len:
        # Degenerate budget: no room for both content and marker. Prefer
        # a visible marker over a silent hard cut, even if it dominates.
        return marker[:max_len]
    keep = max_len - len(marker)
    return s[:keep] + marker


# Each entry: marker name -> compiled pattern, matched against text that
# has already had invisible-formatting codepoints stripped and internal
# whitespace collapsed to single spaces, case-insensitively. `\s+`
# inside a pattern is redundant after collapsing but kept so a pattern
# copied elsewhere without that preprocessing still degrades safely
# rather than silently under-matching.
INJECTION_MARKERS: tuple[tuple[str, re.Pattern], ...] = (
    ("ignore previous instructions",
     re.compile(r"\bignore\s+(?:all\s+|any\s+)?previous\s+instructions\b", re.I)),
    ("disregard the above",
     re.compile(r"\bdisregard\s+(?:all\s+)?the\s+above\b", re.I)),
    ("system prompt",
     re.compile(r"\bsystem\s+prompt\b", re.I)),
    ("reveal/print the secret",
     re.compile(r"\b(?:reveal|print|show|leak)\s+(?:the\s+|your\s+)?secret\b", re.I)),
    ("you are now",
     re.compile(r"\byou\s+are\s+now\b", re.I)),
    ("mark this verified",
     re.compile(r"\bmark\s+this\s+(?:as\s+)?verified\b", re.I)),
    ("delete the receipt",
     re.compile(r"\bdelete\s+the\s+receipt\b", re.I)),
    ("run the following command",
     re.compile(r"\brun\s+the\s+following\s+command\b", re.I)),
    ("grant access",
     re.compile(r"\bgrant\s+access\b", re.I)),
)


def looks_like_injection(text: str) -> tuple[str, ...]:
    """Return the MARKERS FOUND in `text` -- never a boolean verdict.

    This is a blocklist, and a blocklist catches only what someone
    already thought of; see the module docstring for the full honesty
    statement, including what it does and does not do about Unicode
    obfuscation. This function does not decide anything -- it reports
    evidence for a caller to weigh, matching this repository's standing
    discipline (`demand_direction.py`, `activity_shape.py`) that a
    detector never self-certifies its own finding into a verdict.

    An empty tuple means no listed phrase matched. It does not mean the
    text is safe, benign, or cleared.
    """
    if not isinstance(text, str):
        text = str(text)
    normalised = _collapse_whitespace(_strip_invisible_formatting(text))
    return tuple(name for name, pattern in INJECTION_MARKERS
                 if pattern.search(normalised))


@dataclass(frozen=True)
class UntrustedText:
    """The original text, its display-safe rendering, and any markers.

    Frozen and holds `original` verbatim alongside `safe` so a caller
    that only ever touches this object cannot end up storing the
    neutralised copy where evidence belongs, or the raw copy where a
    report gets rendered -- both are always present together. Build one
    with `describe()`, not by hand, so the two stay computed from the
    same input.
    """

    original: str
    safe: str
    markers: tuple[str, ...]


def describe(text: str, max_len: int = DEFAULT_MAX_LEN) -> UntrustedText:
    """Convenience entry point: compute `safe` and `markers` together.

    `text` itself is never touched -- `UntrustedText.original` is the
    exact same string, not a copy that could have drifted. Prefer this
    over calling `neutralise()`/`looks_like_injection()` separately
    whenever both the rendered form and the source evidence need to
    travel together (e.g. into a report line), since it is the version
    of this API that makes losing the original harder to do by accident.
    """
    if not isinstance(text, str):
        text = str(text)
    return UntrustedText(
        original=text,
        safe=neutralise(text, max_len=max_len),
        markers=looks_like_injection(text))
