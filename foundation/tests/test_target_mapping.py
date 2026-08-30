"""A similar name is not an identity, and an empty feed is not a blind eye.

Real data motivated most of these: two of the five targets from the first
live demand sweep have a same-named PyPI package belonging to a different
repository entirely.
"""

import json
import unittest

from foundation.mouth_common import FetchError
from foundation.target_mapping import (
    CONCLUSIVE_MAPPING,
    DirectedObservation,
    MappingIntegrityError,
    TargetMapping,
    candidate_pypi_name,
    direct_observation,
    map_repo_to_pypi,
)


def _pypi(name="widget", urls=None, home=None):
    info = {"name": name, "project_urls": urls or {}}
    if home:
        info["home_page"] = home
    return json.dumps({"info": info}).encode()


def _fetch(payload):
    return lambda url: payload


def _raises(exc):
    def _f(url):
        raise exc
    return _f


def _mapping(**kw):
    base = dict(target="acme/widget", source_class="pypi_releases",
                candidate_identity="widget", state="DECLARED_MATCH",
                declared_repo="acme/widget",
                provenance="the package declares this repository")
    base.update(kw)
    return TargetMapping(**base)


class TestD4NameSimilarityIsNotIdentity(unittest.TestCase):
    def test_the_real_case_a_same_named_package_owned_by_someone_else(self):
        """kubestellar/console vs PyPI `console` (mixmastamyk/console).
        A name match would have invented convergence on live data."""
        m = map_repo_to_pypi("kubestellar/console", _fetch(_pypi(
            "console", {"Homepage": "https://github.com/mixmastamyk/console"})))
        self.assertEqual(m.state, "REFUTED")
        self.assertIn("belongs to a different repository", m.provenance)
        self.assertFalse(m.may_direct_observation())

    def test_a_second_real_case(self):
        """objectionary/eo vs PyPI `eo` (andharris/eo)."""
        m = map_repo_to_pypi("objectionary/eo", _fetch(_pypi(
            "eo", {"Homepage": "https://github.com/andharris/eo"})))
        self.assertEqual(m.state, "REFUTED")

    def test_a_declared_match_is_established_by_the_declaration(self):
        """Positive control: the discipline must not make mapping
        impossible, only unearned."""
        m = map_repo_to_pypi("acme/widget", _fetch(_pypi(
            "widget", {"Source": "https://github.com/acme/widget"})))
        self.assertEqual(m.state, "DECLARED_MATCH")
        self.assertEqual(m.declared_repo, "acme/widget")
        self.assertIn("declares", m.provenance)
        self.assertTrue(m.may_direct_observation())

    def test_the_match_survives_url_noise(self):
        m = map_repo_to_pypi("acme/widget", _fetch(_pypi(
            "widget", {"Source": "https://github.com/ACME/widget.git"})))
        self.assertEqual(m.state, "DECLARED_MATCH")

    def test_home_page_counts_as_a_declaration(self):
        m = map_repo_to_pypi("acme/widget", _fetch(
            _pypi("widget", {}, home="https://github.com/acme/widget")))
        self.assertEqual(m.state, "DECLARED_MATCH")

    def test_a_candidate_name_is_only_ever_a_candidate(self):
        self.assertEqual(candidate_pypi_name("acme/Widget"), "widget")
        self.assertEqual(candidate_pypi_name("no-slash"), "")

    def test_M_a_declared_match_cannot_be_asserted_without_a_declaration(self):
        with self.assertRaises(MappingIntegrityError) as ctx:
            _mapping(declared_repo="")
        self.assertIn("not a declaration", str(ctx.exception))

    def test_M_a_mapping_must_say_how_it_was_established(self):
        with self.assertRaises(MappingIntegrityError) as ctx:
            _mapping(provenance="   ")
        self.assertIn("guess wearing a badge", str(ctx.exception))


class TestD3UnknownIsNotNotFound(unittest.TestCase):
    """Four different facts about the world that one empty list would
    render identical."""

    def test_no_such_package_is_an_answer_not_a_failure(self):
        m = map_repo_to_pypi("acme/widget",
                             _raises(FetchError("HTTP 404 Not Found")))
        self.assertEqual(m.state, "NO_SUCH_PACKAGE")
        self.assertNotEqual(m.state, "LOOKUP_FAILED")

    def test_a_transport_failure_is_not_an_answer(self):
        m = map_repo_to_pypi("acme/widget",
                             _raises(FetchError("connection reset")))
        self.assertEqual(m.state, "LOOKUP_FAILED")
        self.assertIn("whether a mapping exists at all", m.unknowns)

    def test_a_package_declaring_nothing_is_ambiguous_not_refuted(self):
        m = map_repo_to_pypi("acme/widget", _fetch(_pypi("widget", {})))
        self.assertEqual(m.state, "AMBIGUOUS")
        self.assertIn("which repository this package is built from",
                      m.unknowns)

    def test_a_non_repository_target_is_unsupported(self):
        m = map_repo_to_pypi("not-a-repo", _fetch(_pypi()))
        self.assertEqual(m.state, "UNSUPPORTED")

    def test_unparseable_payload_is_a_lookup_failure_not_a_verdict(self):
        m = map_repo_to_pypi("acme/widget", _fetch(b"<html>nope</html>"))
        self.assertEqual(m.state, "LOOKUP_FAILED")

    def test_M_only_established_identity_may_fire_the_instrument(self):
        """Widening this set is a decision to fire blindly, so the guard is
        the PROPERTY, not a frozen literal: every member must be identity
        that was actually established -- asserted by a declaration, or
        definitional because the surface IS the target. Nothing uncertain
        may ever appear here."""
        for state in CONCLUSIVE_MAPPING:
            self.assertIn(state, ("DECLARED_MATCH", "SOURCE_NATIVE"), state)
        for state in ("REFUTED", "NO_SUCH_PACKAGE", "AMBIGUOUS",
                      "UNSUPPORTED", "LOOKUP_FAILED", "UNKNOWN"):
            m = _mapping(state=state, declared_repo="")
            self.assertFalse(m.may_direct_observation(), state)


class TestD1AndD2DirectionAndProvenance(unittest.TestCase):
    class _Obs:
        def __init__(self, items=(), error=None):
            self.new_items = items
            self.error = error

    def test_D1_a_second_instrument_is_pointed_at_a_target_it_never_found(self):
        seen = {}

        def observe(identity):
            seen["identity"] = identity
            return self._Obs(items=({"title": "1.0"},))

        d = direct_observation(_mapping(), observe, "pypi_releases")
        self.assertEqual(d.result, "OBSERVED")
        self.assertEqual(seen["identity"], "widget")
        self.assertTrue(d.saw_something())

    def test_the_mapped_identity_is_used_not_the_original_target(self):
        """The repository path does not address a package index."""
        seen = {}
        direct_observation(_mapping(candidate_identity="pyyaml"),
                           lambda i: seen.setdefault("i", i) or self._Obs(),
                           "pypi_releases")
        self.assertEqual(seen["i"], "pyyaml")
        self.assertNotIn("/", seen["i"])

    def test_D2_the_mapping_provenance_travels_with_the_observation(self):
        d = direct_observation(_mapping(), lambda i: self._Obs(({"a": 1},)),
                               "pypi_releases")
        self.assertIn("declares", d.mapping.provenance)
        self.assertEqual(d.mapping.declared_repo, "acme/widget")

    def test_M_an_unconfirmed_mapping_never_fires_the_instrument(self):
        fired = []
        d = direct_observation(
            _mapping(state="REFUTED", declared_repo=""),
            lambda i: fired.append(i) or self._Obs(), "pypi_releases")
        self.assertEqual(fired, [])
        self.assertEqual(d.result, "MAPPING_NOT_CONCLUSIVE")
        self.assertIn("not fired", d.detail)

    def test_M_empty_and_never_looked_are_different_results(self):
        """The load-bearing distinction. An empty feed is information;
        a mapping that never resolved is not."""
        empty = direct_observation(_mapping(), lambda i: self._Obs(),
                                   "pypi_releases")
        blind = direct_observation(_mapping(state="AMBIGUOUS",
                                            declared_repo=""),
                                   lambda i: self._Obs(), "pypi_releases")
        self.assertEqual(empty.result, "EMPTY")
        self.assertEqual(blind.result, "MAPPING_NOT_CONCLUSIVE")
        self.assertTrue(empty.looked_at_all())
        self.assertFalse(blind.looked_at_all())
        self.assertFalse(empty.saw_something())

    def test_an_unsupported_target_is_reported_as_unsupported(self):
        d = direct_observation(_mapping(state="UNSUPPORTED",
                                        declared_repo=""),
                               lambda i: self._Obs(), "pypi_releases")
        self.assertEqual(d.result, "UNSUPPORTED")

    def test_a_fetch_failure_after_correct_aiming_is_distinct(self):
        def boom(identity):
            raise FetchError("timeout")
        d = direct_observation(_mapping(), boom, "pypi_releases")
        self.assertEqual(d.result, "FETCH_FAILED")
        self.assertIn("pointed correctly", d.detail)

    def test_an_observation_error_field_is_not_ignored(self):
        d = direct_observation(_mapping(),
                               lambda i: self._Obs(error="503"),
                               "pypi_releases")
        self.assertEqual(d.result, "FETCH_FAILED")

    def test_M_a_non_observation_cannot_smuggle_items(self):
        with self.assertRaises(MappingIntegrityError) as ctx:
            DirectedObservation(target="t", instrument="i",
                                result="MAPPING_NOT_CONCLUSIVE",
                                mapping=_mapping(), items=({"a": 1},))
        self.assertIn("smuggle observations", str(ctx.exception))


class TestD5FixedFeedModeSurvives(unittest.TestCase):
    def test_the_github_mouth_still_watches_its_own_feed(self):
        from foundation import mouth_github_releases as gh
        captured = {}

        def fake():
            captured["called"] = True
            return b"<feed></feed>"
        import tempfile, pathlib
        gh.observe(pathlib.Path(tempfile.mkdtemp()) / "s.json", fetch_fn=fake)
        self.assertTrue(captured["called"])

    def test_directing_the_github_mouth_builds_the_target_feed(self):
        from foundation.mouth_github_releases import feed_url_for
        self.assertEqual(feed_url_for("acme/widget"),
                         "https://github.com/acme/widget/releases.atom")

    def test_the_github_mouth_refuses_an_invented_address(self):
        from foundation.mouth_github_releases import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("https://evil.invalid/feed")
        self.assertIn("not at an arbitrary address", str(ctx.exception))

    def test_the_pypi_mouth_refuses_a_repository_path_as_a_package(self):
        """A repository path is not a package identity, and silently
        accepting one is how a wrong mapping becomes a wrong read."""
        from foundation.mouth_pypi import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("acme/widget")
        self.assertIn("not a package identity", str(ctx.exception))

    def test_directing_the_pypi_mouth_builds_the_project_feed(self):
        from foundation.mouth_pypi import feed_url_for
        self.assertEqual(feed_url_for("PyYAML"),
                         "https://pypi.org/rss/project/PyYAML/releases.xml")

    def test_a_directed_observation_is_identifiable_as_directed(self):
        """Fixed and directed reads must not share an identity, or one
        mouth's standing watch and a one-off aim become the same record."""
        from foundation import mouth_pypi as pypi
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mkdtemp())
        fixed = pypi.observe(tmp / "a.json", fetch_fn=lambda: b"<rss></rss>")
        aimed = pypi.observe(tmp / "b.json", fetch_fn=lambda: b"<rss></rss>",
                             target="widget")
        self.assertNotEqual(fixed.mouth_id, aimed.mouth_id)
        self.assertIn("widget", aimed.mouth_id)


if __name__ == "__main__":
    unittest.main()


class TestD6ToD11ConvergenceThroughTheSpine(unittest.TestCase):
    """The steering link is only worth anything if the spine still
    refuses everything it refused before."""

    def setUp(self):
        from datetime import datetime, timedelta, timezone
        self.now = datetime.now(timezone.utc)
        self.fresh = (self.now - timedelta(days=1)).isoformat()
        self.old = (self.now - timedelta(days=400)).isoformat()

    def _demand(self, target="acme/widget", **kw):
        from foundation.signal_spine import CanonicalSignal
        base = dict(
            signal_id="D", source_id="github_help_wanted_issues",
            source_type="PLATFORM", source_ref="https://x.invalid/i/42",
            target=target, kind="DEMAND",
            claim=f"{target}#42 is open and labelled for help",
            observed_at=self.now.isoformat(), event_at=self.fresh,
            source_lineage=f"{target}-issue-42",
            target_established_by="SOURCE_NATIVE",
            facts={"open_help_wanted_issue": "42"},
            pressure_class="EXPLICIT_DEMAND",
            pressure_evidence="labelled help wanted; 12 comments")
        base.update(kw)
        return CanonicalSignal(**base)

    def _directed_release(self, target="acme/widget", **kw):
        from foundation.tentacles import directed_pypi_release_signal
        item = dict(title=kw.pop("version", "2.1.0"),
                    link="https://pypi.invalid/p/widget/2.1.0",
                    pub_date="Sat, 30 Aug 2026 10:00:00 GMT")
        item.update(kw.pop("item", {}))
        s = directed_pypi_release_signal(item, _mapping(target=target), target)
        if kw:
            from dataclasses import replace
            s = replace(s, **kw)
        return s

    def test_D6_real_convergence_is_now_reachable(self):
        """The whole point of the unit: two independent dimensions, one
        mapped target, for the first time."""
        from foundation.signal_spine import fuse, gravity
        f = fuse([self._demand(), self._directed_release()])
        self.assertEqual(f.convergences, 1)
        self.assertEqual(f.corroborations, 0)
        self.assertIn("MULTI_DIMENSIONAL_CONVERGENCE",
                      [k for k, _ in gravity(f).breakdown])

    def test_M_convergence_requires_an_established_target(self):
        """Two signals sharing a string is not two signals about one
        thing."""
        from foundation.signal_spine import fuse
        guessed = self._directed_release(target_established_by="ASSUMED")
        f = fuse([self._demand(), guessed])
        self.assertEqual(f.convergences, 0)

    def test_M_a_signal_cannot_be_built_on_an_unproven_mapping(self):
        from foundation.tentacles import directed_pypi_release_signal
        with self.assertRaises(ValueError) as ctx:
            directed_pypi_release_signal(
                {"title": "1.0"}, _mapping(state="REFUTED", declared_repo=""),
                "acme/widget")
        self.assertIn("guess with a URL attached", str(ctx.exception))

    def test_D7_a_directed_read_of_a_known_release_is_still_one_fact(self):
        """Steering the instrument changes what it looked at, never how
        many times the world happened."""
        from foundation.signal_spine import fuse
        from foundation.tentacles import pypi_release_signal
        directed = self._directed_release(version="2.1.0")
        fixed = pypi_release_signal(
            {"title": "2.1.0", "link": "https://pypi.invalid/p/widget/2.1.0",
             "pub_date": "Sat, 30 Aug 2026 10:00:00 GMT"},
            "widget", "acme/widget")
        f = fuse([directed, fixed])
        self.assertEqual(f.independent_facts, 1)
        self.assertEqual(f.echoes, 1)
        self.assertEqual(f.convergences, 0)

    def test_D8_a_contradiction_still_blocks_the_lock(self):
        from foundation.signal_spine import (fuse, raw_value_map_entry,
                                             target_lock)
        a = self._directed_release(version="2.1.0")
        b = self._directed_release(version="9.9.9", signal_id="OTHER",
                                   source_id="other_index")
        e = raw_value_map_entry(
            fuse([a, b]), why_on_the_map=("two indexes disagree",),
            what_would_kill_it="one index is simply out of date",
            next_cheapest_experiment="read both project pages")
        self.assertEqual(target_lock(e).state, "RESOLVE_CONTRADICTION_FIRST")

    def test_D9_target_direction_creates_no_money_mass(self):
        from foundation.signal_spine import fuse, gravity
        g = gravity(fuse([self._demand(), self._directed_release()]))
        self.assertTrue(g.money_unknown)
        self.assertNotIn("MONEY", " ".join(k for k, _ in g.breakdown))
        self.assertEqual(g.money_observed, "")

    def test_D10_convergence_alone_does_not_bypass_the_lock_gate(self):
        from foundation.signal_spine import (LockNotEarned, fuse,
                                             raw_value_map_entry, target_lock,
                                             to_opportunity)
        e = raw_value_map_entry(
            fuse([self._demand(),
                  self._directed_release()]),
            why_on_the_map=("demand plus a live release",),
            what_would_kill_it="the ask is already claimed",
            next_cheapest_experiment="read the issue thread",
            disqualifiers=("REQUIRES_SECRETS",))
        lock = target_lock(e)
        self.assertEqual(lock.state, "HUMAN_REVIEW_REQUIRED")
        with self.assertRaises(LockNotEarned):
            to_opportunity(e, lock)

    def test_D11_a_directed_read_today_does_not_refresh_an_old_event(self):
        from foundation.signal_spine import fuse
        stale = self._directed_release(event_at=self.old)
        self.assertTrue(stale.is_stale())
        f = fuse([self._demand(), stale])
        self.assertEqual(f.convergences, 0)
        self.assertIn(stale.signal_id, f.stale_signals)

    def test_the_mapping_declaration_travels_into_the_signal(self):
        s = self._directed_release()
        self.assertEqual(s.evidence["mapping_state"], "DECLARED_MATCH")
        self.assertIn("declares", s.evidence["mapping_provenance"])
        self.assertTrue(s.target_is_established())


class TestTheLockSaysWhatItLockedOn(unittest.TestCase):
    """Found live: four help-wanted asks on one repository locked a target
    on single-dimension volume. Not retuned -- made legible."""

    def _asks(self, n):
        from datetime import datetime, timezone
        from foundation.signal_spine import CanonicalSignal
        now = datetime.now(timezone.utc).isoformat()
        return [CanonicalSignal(
            signal_id=f"A{i}", source_id="github_help_wanted_issues",
            source_type="PLATFORM", source_ref=f"https://x.invalid/{i}",
            target="acme/widget", kind="DEMAND",
            claim=f"acme/widget#{i} asks for help",
            observed_at=now, event_at=now,
            source_lineage=f"acme/widget-issue-{i}",
            pressure_class="EXPLICIT_DEMAND",
            pressure_evidence=f"labelled help wanted; {i+3} comments")
            for i in range(n)]

    def _lock(self, sigs):
        from foundation.signal_spine import (fuse, raw_value_map_entry,
                                             target_lock)
        return target_lock(raw_value_map_entry(
            fuse(sigs), why_on_the_map=("open asks",),
            what_would_kill_it="already claimed",
            next_cheapest_experiment="read the threads"))

    def test_M_volume_in_one_dimension_is_named_as_volume(self):
        lock = self._lock(self._asks(4))
        self.assertIn("SINGLE dimension", " ".join(lock.reasons))
        self.assertIn("volume, not cross-dimensional support",
                      " ".join(lock.reasons))

    def test_a_convergent_lock_says_so_instead(self):
        from foundation.tentacles import directed_pypi_release_signal
        rel = directed_pypi_release_signal(
            {"title": "2.1.0", "link": "https://pypi.invalid/x",
             "pub_date": "Sat, 30 Aug 2026 10:00:00 GMT"},
            _mapping(), "acme/widget")
        lock = self._lock(self._asks(1) + [rel])
        self.assertIn("convergent dimension", " ".join(lock.reasons))
        self.assertNotIn("SINGLE dimension", " ".join(lock.reasons))


def _npm(name="widget", repo_url=None, homepage=None, versions=None,
         latest=None):
    doc = {"name": name}
    if repo_url is not None:
        doc["repository"] = {"type": "git", "url": repo_url}
    if homepage:
        doc["homepage"] = homepage
    if versions:
        doc["time"] = dict(versions)
        doc["dist-tags"] = {"latest": latest or sorted(versions)[-1]}
    return json.dumps(doc).encode()


class TestB3AndB4NpmIdentityIsDeclaredNotGuessed(unittest.TestCase):
    """npm makes the discipline matter more, not less: a flat, fifteen-
    year-old namespace collides constantly."""

    def test_B3_the_real_expensify_collision(self):
        """Expensify/App -> npm `app`, declared by rolandpoulter, last
        published 2011. The most expensive false match in the population."""
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("Expensify/App", _fetch(_npm(
            "app", "git://github.com/rolandpoulter/app.git")))
        self.assertEqual(m.state, "REFUTED")
        self.assertIn("rolandpoulter/app", m.provenance)
        self.assertFalse(m.may_direct_observation())

    def test_B3_the_real_screeps_collision(self):
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("tadanobutubutu/screeps", _fetch(_npm(
            "screeps", "git+https://github.com/screeps/screeps.git")))
        self.assertEqual(m.state, "REFUTED")

    def test_B4_the_real_copperhead_match(self):
        """Positive control from the same live population."""
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("copperheadhq/copperhead", _fetch(_npm(
            "copperhead", "git+https://github.com/copperheadhq/copperhead.git")))
        self.assertEqual(m.state, "DECLARED_MATCH")
        self.assertEqual(m.declared_repo, "copperheadhq/copperhead")
        self.assertIn("declares", m.provenance)
        self.assertTrue(m.may_direct_observation())

    def test_B4_mismatching_the_declaration_refutes_the_mapping(self):
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("copperheadhq/copperhead", _fetch(_npm(
            "copperhead", "git+https://github.com/someoneelse/copperhead.git")))
        self.assertEqual(m.state, "REFUTED")

    def test_a_string_repository_field_is_read_too(self):
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("acme/widget",
                            _fetch(json.dumps({
                                "name": "widget",
                                "repository": "https://github.com/acme/widget"
                            }).encode()))
        self.assertEqual(m.state, "DECLARED_MATCH")

    def test_no_declaration_is_ambiguous_not_a_match(self):
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("acme/widget", _fetch(_npm("widget")))
        self.assertEqual(m.state, "AMBIGUOUS")

    def test_no_such_package_is_distinct_from_lookup_failure(self):
        from foundation.target_mapping import map_repo_to_npm
        self.assertEqual(map_repo_to_npm(
            "acme/widget", _raises(FetchError("HTTP Error 404"))).state,
            "NO_SUCH_PACKAGE")
        self.assertEqual(map_repo_to_npm(
            "acme/widget", _raises(FetchError("connection reset"))).state,
            "LOOKUP_FAILED")

    def test_no_second_identity_vocabulary_was_invented(self):
        """DECLARED_MATCH plus provenance already says what an
        NPM_DECLARED_MATCH would say."""
        from foundation.target_mapping import MAPPING_STATES
        for banned in ("NPM_DECLARED_MATCH", "CRATES_DECLARED_MATCH",
                       "SUPER_EXACT_MATCH", "GO_DECLARED_MATCH"):
            self.assertNotIn(banned, MAPPING_STATES)


class TestB2AndB10TargetPreservation(unittest.TestCase):
    def test_B2_two_distinct_targets_resolve_to_distinct_selectors(self):
        from foundation.mouth_npm import feed_url_for
        self.assertNotEqual(feed_url_for("copperhead"), feed_url_for("screeps"))
        self.assertIn("copperhead", feed_url_for("copperhead"))

    def test_B10_the_mouth_cannot_be_aimed_with_a_repository_path(self):
        from foundation.mouth_npm import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("copperheadhq/copperhead")
        self.assertIn("not a package identity", str(ctx.exception))

    def test_the_mouth_requires_a_target_at_all(self):
        from foundation.mouth_npm import feed_url_for
        with self.assertRaises(ValueError):
            feed_url_for("")

    def test_an_unsupported_scoped_package_is_refused_not_guessed(self):
        from foundation.mouth_npm import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("@scope/thing")
        self.assertIn("not supported by this bridge yet", str(ctx.exception))

    def test_the_directed_mouth_id_names_the_target(self):
        from foundation import mouth_npm
        import tempfile, pathlib
        obs = mouth_npm.observe(
            pathlib.Path(tempfile.mkdtemp()) / "s.json", target="copperhead",
            fetch_fn=lambda: _npm("copperhead",
                                  "git+https://github.com/copperheadhq/copperhead.git",
                                  versions={"0.10.0": "2026-08-26T14:03:35Z"}))
        self.assertIn("copperhead", obs.mouth_id)

    def test_B10_a_read_for_one_package_cannot_emit_another(self):
        """The signal's package comes from the MAPPING, not from whatever
        the payload happened to contain."""
        from foundation.tentacles import directed_npm_release_signal
        s = directed_npm_release_signal(
            {"title": "1.0.0", "package": "SOMETHING-ELSE",
             "published_at": "2026-08-26T14:03:35Z", "link": "x"},
            _mapping(candidate_identity="copperhead",
                     target="copperheadhq/copperhead"),
            "copperheadhq/copperhead")
        self.assertIn("copperhead", s.signal_id)
        self.assertNotIn("SOMETHING-ELSE", s.signal_id)
        self.assertNotIn("SOMETHING-ELSE", s.claim)
        self.assertEqual(s.target, "copperheadhq/copperhead")

    def test_M_a_non_conclusive_mapping_cannot_build_an_npm_signal(self):
        from foundation.tentacles import directed_npm_release_signal
        for state in ("REFUTED", "AMBIGUOUS", "NO_SUCH_PACKAGE",
                      "LOOKUP_FAILED", "UNKNOWN", "UNSUPPORTED"):
            with self.assertRaises(ValueError, msg=state):
                directed_npm_release_signal(
                    {"title": "1.0.0"},
                    _mapping(state=state, declared_repo=""), "acme/widget")


class TestB5ToB9NpmThroughTheSpine(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timedelta, timezone
        self.now = datetime.now(timezone.utc)

    def _stamp(self, days):
        from datetime import timedelta
        return (self.now - timedelta(days=days)).isoformat()

    def _demand(self, target="copperheadhq/copperhead"):
        from foundation.signal_spine import CanonicalSignal
        return CanonicalSignal(
            signal_id="D", source_id="github_help_wanted_issues",
            source_type="PLATFORM", source_ref="https://x.invalid/1",
            target=target, kind="DEMAND", claim=f"{target}#7 asks for help",
            observed_at=self.now.isoformat(), event_at=self._stamp(1),
            source_lineage=f"{target}-issue-7",
            pressure_class="EXPLICIT_DEMAND",
            pressure_evidence="labelled help wanted; 6 comments")

    def _npm_sig(self, days=5, version="0.10.0",
                 target="copperheadhq/copperhead"):
        from foundation.tentacles import directed_npm_release_signal
        return directed_npm_release_signal(
            {"title": version, "published_at": self._stamp(days),
             "is_latest": True, "link": "https://npm.invalid/x"},
            _mapping(candidate_identity="copperhead", target=target), target)

    def test_B6_a_second_dimension_is_convergence_not_corroboration(self):
        from foundation.signal_spine import fuse, gravity
        f = fuse([self._demand(), self._npm_sig()])
        self.assertEqual(f.convergences, 1)
        self.assertEqual(f.corroborations, 0)
        labels = [k for k, _ in gravity(f).breakdown]
        self.assertIn("MULTI_DIMENSIONAL_CONVERGENCE", labels)
        self.assertNotIn("INDEPENDENT_CORROBORATION", labels)

    def test_B7_an_npm_publish_of_a_known_release_is_still_one_fact(self):
        """Publishing to a registry is downstream of tagging a release.
        The radar must not count one shipment twice."""
        from foundation.signal_spine import fuse
        from foundation.tentacles import github_release_signal
        gh = github_release_signal(
            {"title": "0.10.0", "link": "https://github.invalid/r",
             "updated": self._stamp(5)},
            "copperhead", "copperheadhq/copperhead")
        f = fuse([gh, self._npm_sig()])
        self.assertEqual(f.independent_facts, 1)
        self.assertEqual(f.echoes, 1)
        self.assertEqual(f.convergences, 0)

    def test_B8_a_stale_publish_read_today_gains_no_fresh_mass(self):
        """The Expensify trap in signal form: a 2011 package read now."""
        from foundation.signal_spine import fuse, gravity
        stale = self._npm_sig(days=400)
        self.assertTrue(stale.is_stale())
        f = fuse([self._demand(), stale])
        self.assertEqual(f.convergences, 0)
        self.assertIn("STALE_EVIDENCE", [k for k, _ in gravity(f).breakdown])

    def test_B9_the_bridge_cannot_manufacture_a_mission(self):
        from foundation.signal_spine import (LockNotEarned, fuse,
                                             raw_value_map_entry, target_lock,
                                             to_opportunity)
        e = raw_value_map_entry(
            fuse([self._demand(), self._npm_sig()]),
            why_on_the_map=("demand plus a live publish",),
            what_would_kill_it="the ask is already claimed",
            next_cheapest_experiment="read the issue thread",
            disqualifiers=("REQUIRES_SECRETS",))
        lock = target_lock(e)
        self.assertEqual(lock.state, "HUMAN_REVIEW_REQUIRED")
        with self.assertRaises(LockNotEarned):
            to_opportunity(e, lock)

    def test_the_bridge_creates_no_money_mass(self):
        from foundation.signal_spine import fuse, gravity
        g = gravity(fuse([self._demand(), self._npm_sig()]))
        self.assertTrue(g.money_unknown)
        self.assertNotIn("MONEY", " ".join(k for k, _ in g.breakdown))

    def test_a_convergent_lock_names_convergence_as_its_basis(self):
        from foundation.signal_spine import (fuse, raw_value_map_entry,
                                             target_lock)
        lock = target_lock(raw_value_map_entry(
            fuse([self._demand(), self._npm_sig()]),
            why_on_the_map=("demand plus a live publish",),
            what_would_kill_it="already claimed",
            next_cheapest_experiment="read the thread"))
        self.assertIn("convergent dimension", " ".join(lock.reasons))


class TestB1TheMouthDoesNotFakeActivity(unittest.TestCase):
    def test_an_unparseable_document_yields_no_versions_not_a_guess(self):
        from foundation.mouth_npm import parse_items
        self.assertEqual(parse_items(b"not json"), ())

    def test_a_package_with_no_releases_parses_to_nothing(self):
        from foundation.mouth_npm import parse_items
        self.assertEqual(parse_items(_npm("widget")), ())

    def test_versions_carry_their_own_publication_time(self):
        from foundation.mouth_npm import parse_items
        items = parse_items(_npm("widget", versions={
            "1.0.0": "2020-01-01T00:00:00Z",
            "2.0.0": "2026-08-26T14:03:35Z"}, latest="2.0.0"))
        self.assertEqual(items[0]["title"], "2.0.0")
        self.assertEqual(items[0]["published_at"], "2026-08-26T14:03:35Z")
        self.assertTrue(items[0]["is_latest"])
        self.assertFalse(items[1]["is_latest"])

    def test_registry_bookkeeping_keys_are_not_versions(self):
        from foundation.mouth_npm import parse_items
        items = parse_items(_npm("widget", versions={
            "created": "2020-01-01T00:00:00Z",
            "modified": "2026-01-01T00:00:00Z",
            "1.0.0": "2021-01-01T00:00:00Z"}, latest="1.0.0"))
        self.assertEqual([i["title"] for i in items], ["1.0.0"])

    def test_the_read_is_bounded(self):
        from foundation.mouth_npm import parse_items, MAX_VERSIONS
        many = {f"1.0.{i}": f"20{10+i:02d}-01-01T00:00:00Z" for i in range(40)}
        self.assertEqual(len(parse_items(_npm("widget", versions=many))),
                         MAX_VERSIONS)


def _commits(*specs):
    """specs: (sha, authored_at, subject)"""
    return json.dumps([
        {"sha": s, "html_url": f"https://github.invalid/c/{s}",
         "commit": {"author": {"date": d}, "message": m}}
        for s, d, m in specs]).encode()


class TestSourceNativeIdentity(unittest.TestCase):
    """No package, no candidate, no guess: the path is the identity."""

    def test_a_repository_is_its_own_identity(self):
        from foundation.target_mapping import source_native_target
        m = source_native_target("acme/widget")
        self.assertEqual(m.state, "SOURCE_NATIVE")
        self.assertEqual(m.candidate_identity, "acme/widget")
        self.assertTrue(m.may_direct_observation())
        self.assertIn("no cross-ecosystem mapping is required", m.provenance)

    def test_M_a_source_native_mapping_cannot_rename_its_target(self):
        from foundation.target_mapping import TargetMapping, MappingIntegrityError
        with self.assertRaises(MappingIntegrityError) as ctx:
            TargetMapping(target="acme/widget", source_class="github_repository",
                          candidate_identity="somethingelse", state="SOURCE_NATIVE",
                          declared_repo="acme/widget", provenance="x")
        self.assertIn("renames its target", str(ctx.exception))

    def test_it_refuses_anything_that_is_not_a_repository_path(self):
        from foundation.target_mapping import source_native_target, MappingIntegrityError
        for bad in ("notarepo", "a/b/c", "  /x", ""):
            with self.assertRaises(MappingIntegrityError):
                source_native_target(bad)

    def test_the_eligibility_set_is_every_repository(self):
        """The whole point, after publication reached 1 in 18."""
        from foundation.target_mapping import source_native_target
        for repo in ("promisszn/soroban-amm", "dotnet/runtime",
                     "AumGupta/abyss-jellyfin", "copperheadhq/copperhead"):
            self.assertTrue(source_native_target(repo).may_direct_observation())

    def test_no_registry_state_can_be_reached_source_natively(self):
        """There is no cross-ecosystem question here, so nothing to refute."""
        from foundation.target_mapping import source_native_target
        m = source_native_target("acme/widget")
        self.assertNotEqual(m.state, "DECLARED_MATCH")
        self.assertNotIn("declares", m.provenance)


class TestTheCommitMouth(unittest.TestCase):
    def test_it_refuses_an_assembled_address(self):
        from foundation.mouth_github_commits import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("https://evil.invalid/x")
        self.assertIn("not at an arbitrary address", str(ctx.exception))

    def test_it_refuses_to_clone_history(self):
        from foundation.mouth_github_commits import feed_url_for
        with self.assertRaises(ValueError) as ctx:
            feed_url_for("acme/widget", 500)
        self.assertIn("does not clone history", str(ctx.exception))

    def test_M_an_error_document_is_not_an_empty_repository(self):
        """The exact unknown-becomes-zero trap, at the parse layer."""
        from foundation.mouth_github_commits import parse_items
        self.assertEqual(parse_items(b'{"message":"Not Found"}'), ())
        self.assertEqual(parse_items(b"not json"), ())

    def test_each_commit_carries_its_own_authored_time(self):
        from foundation.mouth_github_commits import parse_items
        items = parse_items(_commits(
            ("aaa111", "2026-08-30T17:35:39Z", "Merge pull request #244"),
            ("bbb222", "2020-01-01T00:00:00Z", "ancient work")))
        self.assertEqual(items[0]["authored_at"], "2026-08-30T17:35:39Z")
        self.assertEqual(items[1]["authored_at"], "2020-01-01T00:00:00Z")
        self.assertEqual(items[0]["subject"], "Merge pull request #244")

    def test_the_directed_mouth_id_names_the_target(self):
        from foundation import mouth_github_commits as mc
        import tempfile, pathlib
        obs = mc.observe(pathlib.Path(tempfile.mkdtemp()) / "s.json",
                         target="acme/widget",
                         fetch_fn=lambda: _commits(("a1", "2026-08-30T00:00:00Z", "x")))
        self.assertIn("acme/widget", obs.mouth_id)
        self.assertNotEqual(obs.mouth_id, "github_commits")


class TestActivityIsADimensionNotAPlatform(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timezone
        self.now = datetime.now(timezone.utc)

    def _stamp(self, days):
        from datetime import timedelta
        return (self.now - timedelta(days=days)).isoformat()

    def _activity(self, sha="abc123", days=1, subject="fix the thing",
                  target="acme/widget"):
        from foundation.target_mapping import source_native_target
        from foundation.tentacles import repository_activity_signal
        return repository_activity_signal(
            {"sha": sha, "authored_at": self._stamp(days), "subject": subject,
             "link": "https://github.invalid/c"},
            source_native_target(target), target)

    def _demand(self, target="acme/widget", n=1):
        from foundation.signal_spine import CanonicalSignal
        return CanonicalSignal(
            signal_id=f"D{n}", source_id="github_help_wanted_issues",
            source_type="PLATFORM", source_ref="https://x.invalid/i",
            target=target, kind="DEMAND", claim=f"{target}#{n} asks for help",
            observed_at=self.now.isoformat(), event_at=self._stamp(1),
            source_lineage=f"{target}-issue-{n}",
            pressure_class="EXPLICIT_DEMAND",
            pressure_evidence="labelled help wanted; 9 comments")

    def test_the_signal_is_activity_and_claims_nothing_more(self):
        s = self._activity()
        self.assertEqual(s.kind, "ACTIVITY")
        self.assertEqual(s.pressure_class, "NONE")
        self.assertEqual(s.money_claim(), "NOT_MEASURED")
        self.assertEqual(s.target_established_by, "SOURCE_NATIVE")
        self.assertTrue(s.unknowns)

    def test_M_recent_commits_are_not_demand(self):
        """Activity is not someone asking. Never upgrade it."""
        self.assertEqual(self._activity().pressure_class, "NONE")
        self.assertEqual(self._activity(days=0).pressure_class, "NONE")

    def test_M_two_commits_do_not_manufacture_a_contradiction(self):
        """The issue-number defect, deliberately not repeated."""
        from foundation.signal_spine import fuse
        f = fuse([self._activity("aaa", days=1),
                  self._activity("bbb", days=9, subject="other work")])
        self.assertEqual(f.contradictions, ())
        self.assertEqual(f.independent_facts, 2)

    def test_M_two_commits_are_not_two_dimensions(self):
        from foundation.signal_spine import fuse
        f = fuse([self._activity("aaa"), self._activity("bbb", subject="b")])
        self.assertEqual(f.convergences, 0)
        self.assertEqual(f.corroborations, 0)

    def test_M_activity_alone_cannot_manufacture_corroboration(self):
        from foundation.signal_spine import fuse, gravity
        f = fuse([self._activity("aaa"), self._activity("bbb", subject="b"),
                  self._activity("ccc", subject="c")])
        self.assertEqual(f.corroborations, 0)
        self.assertNotIn("INDEPENDENT_CORROBORATION",
                         [k for k, _ in gravity(f).breakdown])

    def test_demand_plus_activity_is_convergence_not_corroboration(self):
        from foundation.signal_spine import fuse, gravity
        f = fuse([self._demand(), self._activity()])
        self.assertEqual(f.convergences, 1)
        self.assertEqual(f.corroborations, 0)
        labels = [k for k, _ in gravity(f).breakdown]
        self.assertIn("MULTI_DIMENSIONAL_CONVERGENCE", labels)
        self.assertNotIn("INDEPENDENT_CORROBORATION", labels)

    def test_M_stale_activity_reread_today_stays_stale(self):
        from foundation.signal_spine import fuse
        old = self._activity(days=400)
        self.assertTrue(old.is_stale())
        self.assertNotEqual(old.event_at[:4], old.observed_at[:4])
        f = fuse([self._demand(), old])
        self.assertEqual(f.convergences, 0)

    def test_M_a_non_conclusive_mapping_cannot_build_an_activity_signal(self):
        from foundation.tentacles import repository_activity_signal
        for state in ("REFUTED", "AMBIGUOUS", "LOOKUP_FAILED", "UNKNOWN"):
            with self.assertRaises(ValueError, msg=state):
                repository_activity_signal(
                    {"sha": "a", "authored_at": "2026-08-30T00:00:00Z"},
                    _mapping(state=state, declared_repo=""), "acme/widget")

    def test_M_a_failed_observation_cannot_create_convergence(self):
        """MAPPING_NOT_CONCLUSIVE carries no items, so there is nothing to
        fuse -- enforced at construction, not by convention."""
        from foundation.target_mapping import (DirectedObservation,
                                               MappingIntegrityError,
                                               source_native_target)
        with self.assertRaises(MappingIntegrityError):
            DirectedObservation(target="acme/widget", instrument="github_commits",
                                result="FETCH_FAILED",
                                mapping=source_native_target("acme/widget"),
                                items=({"sha": "a"},))

    def test_activity_needs_no_package_mapping_at_all(self):
        import foundation.mouth_github_commits as mc
        import ast, inspect
        tree = ast.parse(inspect.getsource(mc))
        imported = {n.module or "" for n in ast.walk(tree)
                    if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("foundation.mouth_npm", imported)
        self.assertNotIn("foundation.mouth_pypi", imported)

    def test_it_reads_no_popularity_metric(self):
        """Stars are easy to fetch and mean nothing. Not fetched.

        Checked against EXECUTABLE code only, with docstrings stripped:
        a source grep otherwise convicts this module for the prose that
        describes the prohibition, which is a test-design trap this project
        has already fallen into once.
        """
        import ast, inspect
        import foundation.mouth_github_commits as mc
        tree = ast.parse(inspect.getsource(mc))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    node.body = node.body[1:]
        code = ast.unparse(tree).lower()
        for vanity in ("stargazers", "stars_count", "forks_count", "watchers",
                       "subscribers_count"):
            self.assertNotIn(vanity, code)


class TestExistingBehaviourSurvives(unittest.TestCase):
    def test_the_pypi_declared_match_path_is_untouched(self):
        m = map_repo_to_pypi("acme/widget", _fetch(_pypi(
            "widget", {"Source": "https://github.com/acme/widget"})))
        self.assertEqual(m.state, "DECLARED_MATCH")

    def test_the_npm_refutation_path_is_untouched(self):
        from foundation.target_mapping import map_repo_to_npm
        m = map_repo_to_npm("Expensify/App", _fetch(_npm(
            "app", "git://github.com/rolandpoulter/app.git")))
        self.assertEqual(m.state, "REFUTED")

    def test_the_fixed_feed_watches_still_run(self):
        from foundation import mouth_github_releases as gh
        import tempfile, pathlib
        obs = gh.observe(pathlib.Path(tempfile.mkdtemp()) / "s.json",
                         fetch_fn=lambda: b"<feed></feed>")
        self.assertEqual(obs.mouth_id, gh.MOUTH_ID)

    def test_conclusive_mapping_widened_only_for_definitional_identity(self):
        from foundation.target_mapping import CONCLUSIVE_MAPPING
        self.assertEqual(set(CONCLUSIVE_MAPPING),
                         {"DECLARED_MATCH", "SOURCE_NATIVE"})
        for never in ("ASSUMED", "AMBIGUOUS", "UNKNOWN", "REFUTED",
                      "NO_SUCH_PACKAGE", "LOOKUP_FAILED", "UNSUPPORTED"):
            self.assertNotIn(never, CONCLUSIVE_MAPPING)
