"""Offline tests for `foundation/capability_profiles.py`.

No network access here -- these tests check the DECLARED DATA is
internally sound (constructible, non-empty, mutually distinct, no
keyword/exclusion collision), not that the live TED evidence in the
module's docstring is still true today. The live evidence was gathered
by hand on 2026-09-01 and is not re-verified by this suite.
"""

import unittest

from foundation.capability_profiles import (
    ALL_PROFILES,
    OLD_GENERIC_IT_PROFILE,
    SECURITY_BROAD_PROFILE,
    SECURITY_CORE_PROFILE,
)
from foundation.relevance import CapabilityProfile


class TestProfilesConstructible(unittest.TestCase):
    """Every declared profile is a real, constructed `CapabilityProfile`."""

    def test_all_are_capability_profile_instances(self):
        for profile in ALL_PROFILES + (OLD_GENERIC_IT_PROFILE,):
            self.assertIsInstance(profile, CapabilityProfile)

    def test_all_profiles_nonempty_declares_something(self):
        # CapabilityProfile.__post_init__ already refuses a profile with
        # no keywords and no cpv_codes -- this test asserts the module
        # actually exercises that path successfully rather than, say,
        # declaring profiles that only ever raise.
        for profile in ALL_PROFILES:
            self.assertTrue(profile.keywords or profile.cpv_codes)

    def test_all_profiles_have_names_and_attribution(self):
        for profile in ALL_PROFILES:
            self.assertTrue(profile.name.strip())
            self.assertTrue(profile.declared_by.strip())


class TestExclusionsAreNontrivial(unittest.TestCase):
    """A profile with an empty exclusion list is a declared footgun --
    every profile this module ships names real noise categories found
    during live research.
    """

    def test_every_profile_declares_exclusions(self):
        for profile in ALL_PROFILES:
            self.assertTrue(
                profile.exclusions,
                f"{profile.name} declares no exclusions",
            )

    def test_exclusions_have_more_than_one_entry(self):
        # A single-term exclusion list is barely better than none --
        # every profile here was built from multiple observed noise
        # categories, not one.
        for profile in ALL_PROFILES:
            self.assertGreater(
                len(profile.exclusions), 1,
                f"{profile.name} has a trivial exclusion list",
            )


class TestNoKeywordExclusionCollision(unittest.TestCase):
    """The real footgun this module's task brief named explicitly: a
    profile that declares the same term as both a positive keyword and
    an exclusion. Since `relevance.score()` checks exclusions FIRST and
    unconditionally, such a term would silently make its own keyword
    dead code -- any notice containing it is EXCLUDED before the
    keyword match is ever consulted.
    """

    def test_no_profile_self_contradicts(self):
        for profile in ALL_PROFILES + (OLD_GENERIC_IT_PROFILE,):
            overlap = profile.keywords & profile.exclusions
            self.assertFalse(
                overlap,
                f"{profile.name} declares {overlap!r} as both a "
                "keyword and an exclusion",
            )

    def test_no_profile_excludes_its_own_cpv_code_as_a_keyword(self):
        # A CPV code and a keyword are different match paths in
        # relevance.py (exact classification field vs free text), so
        # this checks the more literal case: a code that also appears
        # (by string) in keywords or exclusions would be confusing to a
        # future maintainer even though it wouldn't misbehave the same
        # way. Cheap to assert, cheap to keep true.
        for profile in ALL_PROFILES:
            for code in profile.cpv_codes:
                self.assertNotIn(code, profile.exclusions)


class TestProfilesAreDistinct(unittest.TestCase):
    """The whole point of declaring more than one profile is that they
    are actually different instruments -- this catches an accidental
    copy-paste that leaves two profiles scoring identically.
    """

    def test_profiles_have_distinct_names(self):
        names = [p.name for p in ALL_PROFILES + (OLD_GENERIC_IT_PROFILE,)]
        self.assertEqual(len(names), len(set(names)))

    def test_profiles_are_pairwise_distinct_in_content(self):
        profiles = list(ALL_PROFILES) + [OLD_GENERIC_IT_PROFILE]
        for i, a in enumerate(profiles):
            for b in profiles[i + 1:]:
                same_keywords = a.keywords == b.keywords
                same_cpv = a.cpv_codes == b.cpv_codes
                same_exclusions = a.exclusions == b.exclusions
                self.assertFalse(
                    same_keywords and same_cpv and same_exclusions,
                    f"{a.name} and {b.name} declare identical content",
                )

    def test_security_core_is_strictly_narrower_cpv_than_broad(self):
        # The documented relationship between the two new profiles:
        # broad is core's anchor CPV code plus one more, not an
        # unrelated set.
        self.assertTrue(
            SECURITY_CORE_PROFILE.cpv_codes <= SECURITY_BROAD_PROFILE.cpv_codes
        )
        self.assertLess(
            len(SECURITY_CORE_PROFILE.cpv_codes),
            len(SECURITY_BROAD_PROFILE.cpv_codes),
        )


class TestOldProfileRejectedCodesAreAbsent(unittest.TestCase):
    """Documents, as an executable check rather than only prose, that
    the codes this module's docstring says were investigated and
    rejected (too broad, or too dominated by physical-security noise)
    do not silently end up declared anyway.
    """

    REJECTED_CODES = (
        "72000000",  # the umbrella code this module exists to move off
        "72500000", "72600000",  # generic IT, same failure class
        "79710000", "79714000",  # physical guarding/surveillance/CCTV
        "72222000",  # ~15-20% precision, mostly generic IT strategy
        "72810000",  # turned out to mean IT backup, not audit
    )

    def test_new_profiles_do_not_declare_rejected_codes(self):
        for profile in ALL_PROFILES:
            for code in self.REJECTED_CODES:
                self.assertNotIn(
                    code, profile.cpv_codes,
                    f"{profile.name} declares rejected code {code}",
                )

    def test_baseline_profile_still_carries_the_umbrella_code(self):
        # Confirms the comparison reference is what it claims to be --
        # if this ever stops being true the docstring's live-comparison
        # numbers are no longer describing the baseline they say they
        # are.
        self.assertIn("72000000", OLD_GENERIC_IT_PROFILE.cpv_codes)


if __name__ == "__main__":
    unittest.main()
