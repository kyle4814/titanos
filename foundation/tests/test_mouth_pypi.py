import json
import tempfile
import unittest
from pathlib import Path

from foundation.mouth_common import compute_state_hash
from foundation.mouth_pypi import FetchError, observe, parse_items

SAMPLE_RSS_V1 = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>PyPI recent updates for PyYAML</title>
<item>
  <title>6.0.2</title>
  <link>https://pypi.org/project/PyYAML/6.0.2/</link>
  <pubDate>Wed, 03 Sep 2024 00:00:00 GMT</pubDate>
</item>
<item>
  <title>6.0.1</title>
  <link>https://pypi.org/project/PyYAML/6.0.1/</link>
  <guid>https://pypi.org/project/PyYAML/6.0.1/</guid>
  <pubDate>Fri, 18 Jul 2024 00:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""

SAMPLE_RSS_V2_NEW_RELEASE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>PyPI recent updates for PyYAML</title>
<item>
  <title>6.0.3</title>
  <link>https://pypi.org/project/PyYAML/6.0.3/</link>
  <guid>https://pypi.org/project/PyYAML/6.0.3/</guid>
  <pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
</item>
<item>
  <title>6.0.2</title>
  <link>https://pypi.org/project/PyYAML/6.0.2/</link>
  <pubDate>Wed, 03 Sep 2024 00:00:00 GMT</pubDate>
</item>
<item>
  <title>6.0.1</title>
  <link>https://pypi.org/project/PyYAML/6.0.1/</link>
  <guid>https://pypi.org/project/PyYAML/6.0.1/</guid>
  <pubDate>Fri, 18 Jul 2024 00:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""

MALFORMED = b"not xml at all {{{"


class TestParseItems(unittest.TestCase):
    def test_parses_real_shaped_rss(self):
        items = parse_items(SAMPLE_RSS_V1)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "6.0.2")
        # SAMPLE_RSS_V1's first item has no <guid> (matches the real PyPI
        # feed shape) — key must fall back to link.
        self.assertEqual(items[0]["guid"], "")
        self.assertTrue(items[0]["key"].endswith("6.0.2/"))

    def test_malformed_xml_raises_fetch_error(self):
        with self.assertRaises(FetchError):
            parse_items(MALFORMED)


class TestComputeStateHash(unittest.TestCase):
    def test_deterministic(self):
        items = parse_items(SAMPLE_RSS_V1)
        self.assertEqual(compute_state_hash(items), compute_state_hash(items))

    def test_order_independent(self):
        items = parse_items(SAMPLE_RSS_V1)
        reversed_items = tuple(reversed(items))
        self.assertEqual(compute_state_hash(items), compute_state_hash(reversed_items))

    def test_different_items_different_hash(self):
        h1 = compute_state_hash(parse_items(SAMPLE_RSS_V1))
        h2 = compute_state_hash(parse_items(SAMPLE_RSS_V2_NEW_RELEASE))
        self.assertNotEqual(h1, h2)


class TestObserve(unittest.TestCase):
    def test_first_seen_when_no_prior_state(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)
            self.assertEqual(obs.status, "FIRST_SEEN")
            self.assertEqual(obs.item_count, 2)
            self.assertTrue(state_path.exists())

    def test_unchanged_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)
            self.assertEqual(obs.status, "UNCHANGED")
            self.assertEqual(obs.new_items, ())

    def test_changed_identifies_new_items_only(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V2_NEW_RELEASE)
            self.assertEqual(obs.status, "CHANGED")
            self.assertEqual(len(obs.new_items), 1)
            self.assertEqual(obs.new_items[0]["title"], "6.0.3")

    def test_unavailable_preserves_prior_state_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)
            before = state_path.read_text()

            def failing_fetch():
                raise FetchError("simulated outage")

            obs = observe(state_path, fetch_fn=failing_fetch)
            self.assertEqual(obs.status, "UNAVAILABLE")
            self.assertIsNotNone(obs.error)
            self.assertEqual(state_path.read_text(), before)

    def test_unavailable_is_never_treated_as_no_change_after_recovery(self):
        # Prove UNAVAILABLE doesn't corrupt the comparison baseline: after
        # a simulated outage, a real changed state is still detected as
        # CHANGED against the last known-good state, not against nothing.
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V1)

            def failing_fetch():
                raise FetchError("simulated outage")
            observe(state_path, fetch_fn=failing_fetch)

            obs = observe(state_path, fetch_fn=lambda: SAMPLE_RSS_V2_NEW_RELEASE)
            self.assertEqual(obs.status, "CHANGED")

    def test_malformed_feed_is_unavailable_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            obs = observe(state_path, fetch_fn=lambda: MALFORMED)
            self.assertEqual(obs.status, "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
