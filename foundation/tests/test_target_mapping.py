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

    def test_M_only_one_state_may_fire_the_second_instrument(self):
        """Widening this set is a decision to fire blindly."""
        self.assertEqual(CONCLUSIVE_MAPPING, ("DECLARED_MATCH",))
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
