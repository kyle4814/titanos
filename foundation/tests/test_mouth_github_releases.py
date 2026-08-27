import tempfile
import unittest
from pathlib import Path

from foundation.mouth_common import compute_state_hash
from foundation.mouth_github_releases import FetchError, observe, parse_items

SAMPLE_ATOM_V1 = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Release notes from pyyaml</title>
<entry>
  <id>tag:github.com,2008:Repository/2700147/6.0.2</id>
  <title>6.0.2</title>
  <updated>2024-08-06T20:32:48Z</updated>
  <link rel="alternate" type="text/html" href="https://github.com/yaml/pyyaml/releases/tag/6.0.2"/>
</entry>
<entry>
  <id>tag:github.com,2008:Repository/2700147/6.0.1</id>
  <title>6.0.1</title>
  <updated>2023-07-17T23:57:04Z</updated>
  <link rel="alternate" type="text/html" href="https://github.com/yaml/pyyaml/releases/tag/6.0.1"/>
</entry>
</feed>"""

SAMPLE_ATOM_V2_NEW_RELEASE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Release notes from pyyaml</title>
<entry>
  <id>tag:github.com,2008:Repository/2700147/6.0.3</id>
  <title>6.0.3</title>
  <updated>2025-09-25T21:29:27Z</updated>
  <link rel="alternate" type="text/html" href="https://github.com/yaml/pyyaml/releases/tag/6.0.3"/>
</entry>
<entry>
  <id>tag:github.com,2008:Repository/2700147/6.0.2</id>
  <title>6.0.2</title>
  <updated>2024-08-06T20:32:48Z</updated>
  <link rel="alternate" type="text/html" href="https://github.com/yaml/pyyaml/releases/tag/6.0.2"/>
</entry>
</feed>"""

MALFORMED = b"not xml at all {{{"


class TestParseItems(unittest.TestCase):
    def test_parses_real_shaped_atom(self):
        items = parse_items(SAMPLE_ATOM_V1)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "6.0.2")
        self.assertTrue(items[0]["key"].endswith("6.0.2"))

    def test_malformed_xml_raises_fetch_error(self):
        with self.assertRaises(FetchError):
            parse_items(MALFORMED)


class TestComputeStateHash(unittest.TestCase):
    def test_deterministic_and_order_independent(self):
        items = parse_items(SAMPLE_ATOM_V1)
        self.assertEqual(compute_state_hash(items), compute_state_hash(tuple(reversed(items))))

    def test_different_items_different_hash(self):
        h1 = compute_state_hash(parse_items(SAMPLE_ATOM_V1))
        h2 = compute_state_hash(parse_items(SAMPLE_ATOM_V2_NEW_RELEASE))
        self.assertNotEqual(h1, h2)


class TestObserve(unittest.TestCase):
    def test_first_seen_when_no_prior_state(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V1)
            self.assertEqual(obs.status, "FIRST_SEEN")
            self.assertEqual(obs.item_count, 2)

    def test_unchanged_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V1)
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V1)
            self.assertEqual(obs.status, "UNCHANGED")

    def test_changed_identifies_new_items_only(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V1)
            obs = observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V2_NEW_RELEASE)
            self.assertEqual(obs.status, "CHANGED")
            self.assertEqual(obs.new_items[0]["title"], "6.0.3")

    def test_unavailable_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            observe(state_path, fetch_fn=lambda: SAMPLE_ATOM_V1)
            before = state_path.read_text()

            def failing():
                raise FetchError("simulated outage")
            obs = observe(state_path, fetch_fn=failing)
            self.assertEqual(obs.status, "UNAVAILABLE")
            self.assertEqual(state_path.read_text(), before)

    def test_malformed_feed_is_unavailable_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            obs = observe(state_path, fetch_fn=lambda: MALFORMED)
            self.assertEqual(obs.status, "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
