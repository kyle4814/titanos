"""Can a second instrument be pointed at a target the first one found?

WHY THIS IS NOT ENTITY RESOLUTION

There is no knowledge graph here, no ontology, and no universal identity
mesh. There is one question, asked about one pair of source classes: does
the PyPI project that a repository's name suggests actually BELONG to
that repository?

The answer is never derived from the names. A repository name only
produces a CANDIDATE, and a candidate is a guess with a label on it. The
mapping is established -- or refuted -- by the package's own declared
repository URLs, which is the package speaking about itself.

THE REASON THIS MATTERS, MEASURED ON REAL DATA

Two targets from the first live demand sweep both have a same-named PyPI
package owned by somebody else entirely:

    kubestellar/console   -> PyPI `console`  declares mixmastamyk/console
    objectionary/eo       -> PyPI `eo`       declares andharris/eo

A name match would have produced confident, completely false convergence
on two out of five live targets. `REFUTED` exists because of them.

WHAT THE STATES MEAN, AND WHY THEY MAY NOT COLLAPSE

The radar has to know the difference between an instrument that looked
and saw nothing, and an instrument that never had eyes on the target at
all. Those are opposite facts about the world that a single empty list
would render identical:

    DECLARED_MATCH   the package declares this exact repository
    REFUTED          the package exists and belongs to someone else
    NO_SUCH_PACKAGE  nothing is published under that candidate name
    AMBIGUOUS        several declared repositories, none decisive
    UNSUPPORTED      this source class cannot address this kind of target
    LOOKUP_FAILED    the question could not be asked
    UNKNOWN          not attempted

Only DECLARED_MATCH may carry a directed observation. Everything else
stops the second instrument from firing blindly.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from foundation.mouth_common import DEFAULT_TIMEOUT_SECONDS, FetchError, fetch_feed
from foundation.discovery_authorization import DiscoveryPolicy

__all__ = [
    "MAPPING_STATES", "CONCLUSIVE_MAPPING", "OBSERVATION_RESULTS",
    "TargetMapping", "candidate_pypi_name", "map_repo_to_pypi",
    "MappingIntegrityError", "DirectedObservation", "direct_observation",
    "map_repo_to_npm", "source_native_target",
]

# The concrete objective this module fetches for. `fetch_feed()`
# refuses to open a socket without one -- see its docstring for why
# the gate lives at the socket rather than above it.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective="resolve one named repository to its package-registry identity",
    requested_scope="READ_API")


class MappingIntegrityError(ValueError):
    """A mapping tried to claim identity it did not establish."""


MAPPING_STATES = ("DECLARED_MATCH", "SOURCE_NATIVE", "REFUTED",
                  "NO_SUCH_PACKAGE", "AMBIGUOUS", "UNSUPPORTED",
                  "LOOKUP_FAILED", "UNKNOWN")

# The only state that earns a directed read. Deliberately a single value:
# every widening of this set is a decision to fire an instrument at a
# target nobody confirmed.
# Widened once, deliberately, and only for identity that is DEFINITIONAL
# rather than asserted: when the surface being read is the repository
# itself, there is no cross-ecosystem question to get wrong. The tight
# constructor `source_native_target()` is the only way to obtain it, and it
# refuses anything that is not an owner/name path.
CONCLUSIVE_MAPPING = ("DECLARED_MATCH", "SOURCE_NATIVE")

# How a directed observation ended. "Saw nothing" and "never looked" are
# different facts and never share a value.
OBSERVATION_RESULTS = ("OBSERVED", "EMPTY", "MAPPING_NOT_CONCLUSIVE",
                       "UNSUPPORTED", "FETCH_FAILED")

_PYPI_JSON = "https://pypi.org/pypi/{name}/json"
_GITHUB_REPO = re.compile(r"github\.com/([^/\s]+)/([^/\s#?]+)", re.I)


@dataclass(frozen=True)
class TargetMapping:
    """One target, one secondary source class, and how we know.

    `evidence` is what was actually observed -- the declared URLs -- not a
    summary of them. `provenance` says which act established the mapping,
    so a later reader never has to guess whether a name or a declaration
    was doing the work.
    """

    target: str
    source_class: str
    candidate_identity: str
    state: str
    provenance: str
    evidence: tuple[str, ...] = ()
    declared_repo: str = ""
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in MAPPING_STATES:
            raise MappingIntegrityError(f"unknown mapping state {self.state!r}")
        if not self.provenance.strip():
            raise MappingIntegrityError(
                "a mapping must say how it was established; an unexplained "
                "identity is a guess wearing a badge")
        if self.state == "SOURCE_NATIVE" and (
                self.candidate_identity != self.target
                or self.declared_repo != self.target):
            raise MappingIntegrityError(
                "SOURCE_NATIVE means the target IS the identity; a source-"
                "native mapping that renames its target is a contradiction")
        if self.state == "DECLARED_MATCH" and not self.declared_repo:
            raise MappingIntegrityError(
                "DECLARED_MATCH requires the declaration that established "
                "it; a name similarity is not a declaration")

    def is_conclusive(self) -> bool:
        return self.state in CONCLUSIVE_MAPPING

    def may_direct_observation(self) -> bool:
        """The gate. Only a conclusive mapping points a second eye."""
        return self.is_conclusive()

    def show_the_reasoning(self) -> str:
        lines = [f"TARGET {self.target} -> {self.source_class}",
                 f"  candidate   {self.candidate_identity or 'none'}",
                 f"  state       {self.state}",
                 f"  provenance  {self.provenance}"]
        if self.declared_repo:
            lines.append(f"  declared    {self.declared_repo}")
        for e in self.evidence:
            lines.append(f"  observed    {e}")
        for u in self.unknowns:
            lines.append(f"  unknown     {u}")
        return "\n".join(lines)


def _normalise_repo(url: str) -> str:
    m = _GITHUB_REPO.search(url or "")
    if not m:
        return ""
    owner, name = m.group(1), m.group(2)
    return f"{owner.lower()}/{re.sub(r'\.git$', '', name).lower()}"


def candidate_pypi_name(repo: str) -> str:
    """Derive a CANDIDATE package name from a repository name.

    This is a guess and is treated as one everywhere it is used. It exists
    only to have something to ask PyPI about; it never establishes
    anything on its own.
    """
    if "/" not in repo:
        return ""
    return repo.split("/", 1)[1].strip().lower()


def map_repo_to_pypi(repo: str,
                     fetch_fn: Optional[Callable[[str], bytes]] = None,
                     ) -> TargetMapping:
    """Ask PyPI whether it hosts a package that claims this repository.

    The candidate name comes from the repository; the ANSWER comes from
    the package's declared URLs. If the package exists but points
    somewhere else, that is REFUTED -- an actively wrong mapping, which is
    far more useful to know than an absent one.
    """
    fetch = fetch_fn or (lambda url: fetch_feed(url, DEFAULT_TIMEOUT_SECONDS, policy=DISCOVERY_POLICY))
    want = _normalise_repo(f"github.com/{repo}")
    candidate = candidate_pypi_name(repo)

    if not candidate or not want:
        return TargetMapping(
            target=repo, source_class="pypi_releases", candidate_identity="",
            state="UNSUPPORTED",
            provenance="target is not an owner/name repository, so no PyPI "
                       "candidate can be derived at all")

    try:
        raw = fetch(_PYPI_JSON.format(name=candidate))
    except FetchError as exc:
        text = str(exc)
        # A 404 is an ANSWER -- nothing is published under that name --
        # and must not be filed as a failure to ask.
        if "404" in text:
            return TargetMapping(
                target=repo, source_class="pypi_releases",
                candidate_identity=candidate, state="NO_SUCH_PACKAGE",
                provenance=f"PyPI has no project named {candidate!r}",
                evidence=(f"lookup returned 404 for {candidate}",))
        return TargetMapping(
            target=repo, source_class="pypi_releases",
            candidate_identity=candidate, state="LOOKUP_FAILED",
            provenance=f"the question could not be asked: {text[:120]}",
            unknowns=("whether a mapping exists at all",))

    try:
        info = json.loads(raw)["info"]
    except (ValueError, KeyError, TypeError):
        return TargetMapping(
            target=repo, source_class="pypi_releases",
            candidate_identity=candidate, state="LOOKUP_FAILED",
            provenance="PyPI returned a payload this reader could not parse",
            unknowns=("whether a mapping exists at all",))

    urls = dict(info.get("project_urls") or {})
    if info.get("home_page"):
        urls["home_page"] = info["home_page"]
    declared = {}
    for label, url in urls.items():
        norm = _normalise_repo(str(url))
        if norm:
            declared.setdefault(norm, []).append(f"{label}={url}")

    evidence = tuple(sorted(v for vals in declared.values() for v in vals))

    if want in declared:
        return TargetMapping(
            target=repo, source_class="pypi_releases",
            candidate_identity=info.get("name", candidate),
            state="DECLARED_MATCH", declared_repo=want,
            provenance=(f"PyPI project {info.get('name', candidate)!r} "
                        f"declares {want} among its own project URLs"),
            evidence=evidence)

    if not declared:
        return TargetMapping(
            target=repo, source_class="pypi_releases",
            candidate_identity=info.get("name", candidate),
            state="AMBIGUOUS",
            provenance=(f"a project named {candidate!r} exists but declares "
                        f"no repository, so nothing connects it to {repo}"),
            evidence=evidence,
            unknowns=("which repository this package is built from",))

    return TargetMapping(
        target=repo, source_class="pypi_releases",
        candidate_identity=info.get("name", candidate),
        state="REFUTED",
        provenance=(f"a project named {candidate!r} exists but declares "
                    f"{', '.join(sorted(declared))} -- it belongs to a "
                    f"different repository, not {repo}"),
        evidence=evidence)


@dataclass(frozen=True)
class DirectedObservation:
    """The result of pointing a second instrument at a discovered target.

    `result` never collapses. An empty release feed means the project
    publishes no releases; MAPPING_NOT_CONCLUSIVE means the instrument was
    never fired because nobody established it was looking at the right
    thing. Reporting both as "no signal" would tell the radar the same
    story about two opposite situations.
    """

    target: str
    instrument: str
    result: str
    mapping: TargetMapping
    items: tuple[dict, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        if self.result not in OBSERVATION_RESULTS:
            raise MappingIntegrityError(
                f"unknown observation result {self.result!r}")
        if self.items and self.result != "OBSERVED":
            raise MappingIntegrityError(
                f"result {self.result!r} carries {len(self.items)} items; a "
                f"non-observation cannot smuggle observations")

    def saw_something(self) -> bool:
        return self.result == "OBSERVED"

    def looked_at_all(self) -> bool:
        """Distinct from `saw_something`. An instrument that looked and
        found an empty feed learned something; one that never fired did
        not."""
        return self.result in ("OBSERVED", "EMPTY")


def direct_observation(mapping: TargetMapping, observe_fn: Callable[[str], object],
                       instrument: str) -> DirectedObservation:
    """Fire the second instrument -- but only at a confirmed target.

    `observe_fn` receives the mapped identity, not the original target,
    because the whole point of the mapping is that those are different
    names for one thing and only one of them addresses this source class.
    """
    if not mapping.may_direct_observation():
        return DirectedObservation(
            target=mapping.target, instrument=instrument,
            result=("UNSUPPORTED" if mapping.state == "UNSUPPORTED"
                    else "MAPPING_NOT_CONCLUSIVE"),
            mapping=mapping,
            detail=(f"not fired: mapping is {mapping.state}. "
                    f"{mapping.provenance}"))
    try:
        observation = observe_fn(mapping.candidate_identity)
    except FetchError as exc:
        return DirectedObservation(
            target=mapping.target, instrument=instrument,
            result="FETCH_FAILED", mapping=mapping,
            detail=f"the instrument was pointed correctly but could not "
                   f"read: {str(exc)[:140]}")

    items = tuple(getattr(observation, "new_items", ()) or ())
    if getattr(observation, "error", None):
        return DirectedObservation(
            target=mapping.target, instrument=instrument,
            result="FETCH_FAILED", mapping=mapping,
            detail=str(observation.error)[:140])
    if not items:
        return DirectedObservation(
            target=mapping.target, instrument=instrument, result="EMPTY",
            mapping=mapping,
            detail="the instrument looked at the confirmed target and the "
                   "source published nothing")
    return DirectedObservation(
        target=mapping.target, instrument=instrument, result="OBSERVED",
        mapping=mapping, items=items,
        detail=f"{len(items)} item(s) from the confirmed target")


_NPM_JSON = "https://registry.npmjs.org/{name}"


def candidate_npm_name(repo: str) -> str:
    """A CANDIDATE npm package name. Same status as the PyPI candidate: a
    guess whose only job is to give the registry something to answer."""
    if "/" not in repo:
        return ""
    return repo.split("/", 1)[1].strip().lower()


def _declared_repo_urls(payload: dict) -> dict[str, list[str]]:
    """Every repository an npm document declares, however it spells it."""
    declared: dict[str, list[str]] = {}
    candidates = []
    rep = payload.get("repository")
    if isinstance(rep, dict):
        candidates.append(("repository.url", rep.get("url", "")))
    elif isinstance(rep, str):
        candidates.append(("repository", rep))
    if payload.get("homepage"):
        candidates.append(("homepage", payload["homepage"]))
    for label, url in candidates:
        norm = _normalise_repo(str(url))
        if norm:
            declared.setdefault(norm, []).append(f"{label}={url}")
    return declared


def map_repo_to_npm(repo: str,
                    fetch_fn: Optional[Callable[[str], bytes]] = None,
                    ) -> TargetMapping:
    """Ask the npm registry whether it hosts a package claiming this repo.

    Identical discipline to `map_repo_to_pypi`, and deliberately the same
    vocabulary -- DECLARED_MATCH plus provenance already says exactly what
    an `NPM_DECLARED_MATCH` would say, so no second identity vocabulary is
    invented here.

    npm makes the discipline matter MORE, not less. Its namespace is flat
    and old, so short repository names collide constantly: `Expensify/App`
    resolves to an npm package `app` that declares rolandpoulter/app and
    was last published in 2011, and `tadanobutubutu/screeps` resolves to a
    package declaring screeps/screeps. Both are REFUTED here; both would
    have been confident false convergence under name matching.
    """
    fetch = fetch_fn or (lambda url: fetch_feed(url, DEFAULT_TIMEOUT_SECONDS, policy=DISCOVERY_POLICY))
    want = _normalise_repo(f"github.com/{repo}")
    candidate = candidate_npm_name(repo)

    if not candidate or not want:
        return TargetMapping(
            target=repo, source_class="npm_releases", candidate_identity="",
            state="UNSUPPORTED",
            provenance="target is not an owner/name repository, so no npm "
                       "candidate can be derived at all")

    try:
        raw = fetch(_NPM_JSON.format(name=candidate))
    except FetchError as exc:
        text = str(exc)
        if "404" in text:
            return TargetMapping(
                target=repo, source_class="npm_releases",
                candidate_identity=candidate, state="NO_SUCH_PACKAGE",
                provenance=f"the npm registry has no package named "
                           f"{candidate!r}",
                evidence=(f"lookup returned 404 for {candidate}",))
        return TargetMapping(
            target=repo, source_class="npm_releases",
            candidate_identity=candidate, state="LOOKUP_FAILED",
            provenance=f"the question could not be asked: {text[:120]}",
            unknowns=("whether a mapping exists at all",))

    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return TargetMapping(
            target=repo, source_class="npm_releases",
            candidate_identity=candidate, state="LOOKUP_FAILED",
            provenance="the registry returned a payload this reader could "
                       "not parse",
            unknowns=("whether a mapping exists at all",))

    name = payload.get("name", candidate)
    declared = _declared_repo_urls(payload)
    evidence = tuple(sorted(v for vals in declared.values() for v in vals))

    if want in declared:
        return TargetMapping(
            target=repo, source_class="npm_releases", candidate_identity=name,
            state="DECLARED_MATCH", declared_repo=want,
            provenance=(f"npm package {name!r} declares {want} as its own "
                        f"repository"),
            evidence=evidence)

    if not declared:
        return TargetMapping(
            target=repo, source_class="npm_releases", candidate_identity=name,
            state="AMBIGUOUS",
            provenance=(f"an npm package named {candidate!r} exists but "
                        f"declares no repository, so nothing connects it to "
                        f"{repo}"),
            evidence=evidence,
            unknowns=("which repository this package is published from",))

    return TargetMapping(
        target=repo, source_class="npm_releases", candidate_identity=name,
        state="REFUTED",
        provenance=(f"an npm package named {candidate!r} exists but declares "
                    f"{', '.join(sorted(declared))} -- it belongs to a "
                    f"different repository, not {repo}"),
        evidence=evidence)


def source_native_target(repo: str) -> TargetMapping:
    """Identity for a surface that IS the repository.

    No candidate, no guess, no registry: reading a repository's own commits
    asks no cross-ecosystem question at all, so there is nothing here that
    could be REFUTED. This is why the state is SOURCE_NATIVE and not
    DECLARED_MATCH -- nobody declared anything; the path is the identity.

    The eligibility set is therefore every repository target, which is the
    entire point after publication-based observation reached 1 in 18.
    """
    if repo.count("/") != 1 or not all(p.strip() for p in repo.split("/")):
        raise MappingIntegrityError(
            f"expected an owner/name repository path, got {repo!r}; a "
            f"source-native identity cannot be derived from anything else")
    return TargetMapping(
        target=repo, source_class="github_repository", candidate_identity=repo,
        state="SOURCE_NATIVE", declared_repo=repo,
        provenance=("the repository path is itself the target identity; no "
                    "cross-ecosystem mapping is required or possible"))
