# Testing

## Current counts (2026-08-25, all passing)

| Suite | Tests | Focus |
|---|---|---|
| `schema/tests/test_validator.py` | 22 | core structural validation |
| `schema/tests/test_false_negatives.py` | 24 | adversarial bypass attempts, §Phase 4 |
| `schema/tests/test_meta_attack.py` | 13 | attacks against the validator/gate itself, §Phase 5 |
| `schema/tests/test_real_corpus_regressions.py` | 5 | bugs found running against the real 3,058-file corpus |
| `schema/tests/test_no_network.py` | 3 | AST scan: no network/exec imports |
| `firewall/tests/test_firewall.py` | 19 | gate.py — narrative cannot authorize, etc. |
| `firewall/tests/test_quarantine_dissent.py` | 17 | quarantine + dissent mechanisms |
| `legacy/tests/test_classify.py` | 7 | legacy classification tool (synthetic files) |
| **Total** | **110** | |

Run everything: `python3 -m unittest discover -s schema -p "test_*.py"`,
`python3 -m unittest discover -s firewall/tests`,
`python3 -m unittest discover -s legacy/tests`.

## Rule: no fix without a regression test

Every bug found in this session became a permanent test:
`RecursionError` on deep alias chains (`test_false_negatives.py`), and the
non-string-key `TypeError` found running against real legacy data
(`test_real_corpus_regressions.py`). Both were discovered by actually
running the code against adversarial or real input, not by inspection.

## What is deliberately NOT covered

- End-to-end pipeline tests (no pipeline exists yet — see
  `ARCHITECTURE.md`).
- Load/performance testing at corpus scale beyond the single real run
  documented in `legacy/DECISION_PACKET.md` (~3 minutes for 3,058 files,
  single-threaded, one-time).
- Property-based (hypothesis-style) testing. The directive asked for it
  "where useful" — no property-based test was judged to add coverage the
  existing adversarial suite doesn't already provide for this size of
  codebase, so none was added rather than added for the appearance of
  completeness.
