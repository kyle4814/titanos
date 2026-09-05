"""Tests for `foundation/lead_source.py` — CSV → business domains.

Pure parsing, no network. Synthetic CSV only (never the operator's real data)."""

import unittest

from foundation.lead_source import domains_from_csv, FREE_EMAIL_PROVIDERS

CSV = (
    "business_name,email,website,category,state\n"
    'Acme Plumbing,info@acmeplumbing.com.au,https://www.acmeplumbing.com.au/contact,trades,QLD\n'
    'Bob Cafe,bobscafe@gmail.com,,food,QLD\n'
    'Cyber Co,,http://cyberco.io,it,NSW\n'
    'Dupe Ltd,x@acmeplumbing.com.au,acmeplumbing.com.au,trades,QLD\n'
    'No Web No Biz Email,someone@outlook.com,,misc,VIC\n'
    'Email Only,contact@emailonly.com.au,,services,WA\n'
)


class TestDomainsFromCsv(unittest.TestCase):
    def test_extracts_and_normalises_website_domains(self):
        doms = domains_from_csv(CSV)
        self.assertIn("acmeplumbing.com.au", doms)   # https+www+path stripped
        self.assertIn("cyberco.io", doms)

    def test_email_fallback_when_no_website(self):
        doms = domains_from_csv(CSV)
        self.assertIn("emailonly.com.au", doms)      # from the email column

    def test_free_mail_providers_are_dropped(self):
        doms = domains_from_csv(CSV)
        self.assertNotIn("gmail.com", doms)
        self.assertNotIn("outlook.com", doms)
        self.assertTrue(FREE_EMAIL_PROVIDERS)         # the set is populated

    def test_dedup_preserves_first_occurrence(self):
        doms = domains_from_csv(CSV)
        self.assertEqual(doms.count("acmeplumbing.com.au"), 1)

    def test_limit_takes_a_polite_batch(self):
        doms = domains_from_csv(CSV, limit=2)
        self.assertEqual(len(doms), 2)

    def test_empty_or_headeronly_csv_is_empty(self):
        self.assertEqual(domains_from_csv(""), [])
        self.assertEqual(domains_from_csv("business_name,email\n"), [])

    def test_junk_website_values_are_skipped(self):
        junk = ("name,website\n"
                "A,not a url\n"
                "B,localhost\n"
                "C,realbiz.com\n")
        self.assertEqual(domains_from_csv(junk), ["realbiz.com"])


if __name__ == "__main__":
    unittest.main()
