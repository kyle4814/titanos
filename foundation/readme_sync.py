"""Recompute README.md's declared test count from the real tests.

WHY THIS EXISTS

`sentinel.check_readme_test_count()` observes that README's hand-written
number has drifted from the real one. It is deliberately incapable of
fixing it -- Sentinel_141 is structurally forbidden from executing its
own findings, and `TestSentinelCannotExecute` enforces that by scanning
its public callables for action verbs. So the observation is correct and
nothing acts on it.

The result: the same finding broke the build three times across two work
cells, each time because a human added tests and forgot a number in
prose. That is a recurring defect with a known cause, not bad luck, and
the doctrine's own rule for a recurring failure is to mutate the system
rather than repeat the repair.

This module is the missing writer, kept OUT of `sentinel.py` on purpose:
the sensor observes, this acts, and the separation stays legible.

WHAT IT DOES NOT DO

It does not run any tests and it does not verify they pass. It counts
`def test_` definitions -- exactly the same quantity the sentinel
compares against, so the two cannot disagree about what is being
measured. A green count is not a green suite, and README says so
already.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["count_test_definitions", "read_declared_count",
           "render_count", "sync_readme_test_count"]

# The README sentence this module owns. Matched loosely on the number so
# a reworded sentence still updates, and anchored on "tests across" so it
# cannot match an unrelated figure elsewhere in the file.
_DECLARED = re.compile(r"\*\*([\d,]+) tests across")

def count_test_definitions(repo_root: Path) -> int:
    """Delegates to `sentinel.count_real_tests()`. Never reimplements it.

    The first draft of this module counted `def test_` under any
    `tests/` directory, while the sentinel counts files named
    `test_*.py` anywhere outside its excluded dirs. The two disagreed by
    5 on the real repository, and a writer that disagrees with the
    sensor it is supposed to satisfy would leave the finding permanently
    open -- each run "fixing" the number back to a value the sensor
    still rejects.

    Caught by this module's own test asserting the two agree. Fixed by
    deleting the second implementation rather than reconciling it: the
    sensor defines the quantity, this module only writes it down.
    """
    from foundation.sentinel import count_real_tests
    return count_real_tests(Path(repo_root))


def read_declared_count(readme: Path) -> int | None:
    match = _DECLARED.search(Path(readme).read_text(errors="ignore"))
    return int(match.group(1).replace(",", "")) if match else None


def render_count(n: int) -> str:
    return f"{n:,}"


def sync_readme_test_count(repo_root: Path, dry_run: bool = False) -> dict:
    """Bring README's number in line with the real one.

    Returns what changed rather than printing, so a caller can receipt
    it. `dry_run` reports the delta without writing -- the same call a
    pre-commit check would make.
    """
    repo_root = Path(repo_root)
    readme = repo_root / "README.md"
    if not readme.is_file():
        return {"status": "NO_README", "path": str(readme)}

    real = count_test_definitions(repo_root)
    declared = read_declared_count(readme)
    if declared is None:
        return {"status": "NO_CLAIM_FOUND", "real": real,
                "note": "README does not declare a test count; nothing to sync"}
    if declared == real:
        return {"status": "ALREADY_CURRENT", "real": real, "declared": declared}
    if dry_run:
        return {"status": "WOULD_UPDATE", "real": real, "declared": declared,
                "delta": real - declared}

    text = readme.read_text()
    readme.write_text(
        _DECLARED.sub(f"**{render_count(real)} tests across", text, count=1))
    return {"status": "UPDATED", "real": real, "declared": declared,
            "delta": real - declared}


if __name__ == "__main__":                                # pragma: no cover
    import sys
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    result = sync_readme_test_count(root, dry_run="--check" in sys.argv)
    print(f"README test count: {result}")
    sys.exit(1 if result["status"] == "WOULD_UPDATE" else 0)
