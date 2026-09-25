"""Ring 0 boundary: boot fail-closed, cross-process single use, one chokepoint.

Every claim here is proven against real mechanisms, not mocks of them:
  - boot reads TITANOS_RING0_SECRET through the production loader;
  - replay protection is the SQLite file itself, exercised by two separate
    Python processes (cold restart) and by N concurrent processes (race);
  - the chokepoint is checked by scanning the production source tree.
"""

import ast
import json
import multiprocessing
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from foundation.adapter_execution_gateway import AdapterExecutionGateway, boot_gateway
from foundation.approval_envelope import (
    AlreadyConsumedError, ApprovalEnvelope, ApprovalError, ConsumedIds,
    ConsumptionUnavailable, RING0_SECRET_ENV, Ring0SecretError, load_ring0_key,
)
from foundation.authorization_gate import ApprovalReplayed, AuthorizationGate
from foundation.execution_dispatcher import AdapterDispatchError, AdapterDispatcher
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt_store import ExecutionReceiptStore

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SECRET = "r0-" + "0123456789abcdef" * 3           # test-only, 51 bytes, not a dev value
RACE_N = 8


def _intent():
    return ExecutionIntent(
        intent_id="EI-RING0-1", target="fake:acct-9", action="CREATE_LINK",
        parameters={"amount": 42}, evidence_refs=("OPP-9",),
        expected_effect="one link", authority_required="A3", reversible=True,
        expires_at="2099-01-01T00:00:00+00:00", policy_version="p-1")


def _signed_envelope_dict(nonce="ring0-nonce-1"):
    env = ApprovalEnvelope.decide(
        proposal_id="p9", intent=_intent(), decision="APPROVE", authority="A3",
        reviewer="kyle", decided_at="2026-09-25T00:00:00+00:00", nonce=nonce)
    return env.signed(SECRET.encode()).to_dict()


def _attempt(db_path: str, envelope: dict) -> str:
    """One contender, as a fresh process would run it: production key
    loader, the on-disk ledger, the real gate. Returns a classification."""
    try:
        key = load_ring0_key()
        AuthorizationGate.issue(_intent(), ApprovalEnvelope(**envelope), key=key,
                                consumed=ConsumedIds(Path(db_path)))
        return "SUCCESS"
    except ApprovalReplayed:
        return "ALREADY_CONSUMED"
    except Exception as exc:  # noqa: BLE001 -- classified, never hidden
        return f"UNEXPECTED:{type(exc).__name__}:{exc}"


def _race_worker(db_path, envelope, barrier, results):
    barrier.wait(timeout=60)
    results.put(_attempt(db_path, envelope))


class TestBootFailsClosed(unittest.TestCase):

    def test_missing_secret_hard_fails(self):
        for env in ({}, {RING0_SECRET_ENV: ""}, {RING0_SECRET_ENV: "   "}):
            with self.assertRaisesRegex(Ring0SecretError, "not set"):
                load_ring0_key(env)

    def test_dev_or_weak_secret_hard_fails(self):
        for bad in ("changeme", "titanos-dev-secret", "DEV", "short-but-real",
                    "k" * 64):
            with self.assertRaises(Ring0SecretError, msg=bad):
                load_ring0_key({RING0_SECRET_ENV: bad})

    def test_valid_secret_boots(self):
        self.assertEqual(load_ring0_key({RING0_SECRET_ENV: SECRET}), SECRET.encode())

    def test_boot_fails_before_ledger_or_adapters_are_touched(self):
        touched = []

        def adapters():
            touched.append("adapters")
            yield from ()

        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "consumed.db"
            with self.assertRaises(Ring0SecretError):
                boot_gateway(adapters(), ExecutionReceiptStore(Path(d) / "r.json"),
                             ledger, environ={})
            self.assertFalse(ledger.exists())
        self.assertEqual(touched, [])

    def test_valid_boot_builds_a_gateway(self):
        with tempfile.TemporaryDirectory() as d:
            gw = boot_gateway([], ExecutionReceiptStore(Path(d) / "r.json"),
                              Path(d) / "consumed.db", environ={RING0_SECRET_ENV: SECRET})
            self.assertIsInstance(gw, AdapterExecutionGateway)

    def test_a_gateway_cannot_be_built_with_a_bad_key(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in (b"", b"short", None):
                with self.assertRaises(ApprovalError):
                    AdapterExecutionGateway(
                        AdapterDispatcher.from_adapters([]),
                        ExecutionReceiptStore(Path(d) / "r.json"), bad,
                        ConsumedIds(Path(d) / "c.db"))

    def test_process_local_ledgers_are_refused(self):
        for bad in (None, "", ":memory:"):
            with self.assertRaises(ApprovalError):
                ConsumedIds(bad)


class TestSqliteSingleUse(unittest.TestCase):

    def test_schema_has_a_primary_key_on_id(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "c.db"
            ConsumedIds(db)
            conn = sqlite3.connect(db)
            cols = conn.execute("PRAGMA table_info(consumed_ids)").fetchall()
            conn.close()
        self.assertEqual([c[1] for c in cols if c[5] == 1], ["id"])

    def test_second_consume_is_a_domain_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = ConsumedIds(Path(d) / "c.db")
            ledger.consume("approval:x")
            with self.assertRaises(AlreadyConsumedError):
                ConsumedIds(Path(d) / "c.db").consume("approval:x")
            self.assertEqual(ledger.count("approval:x"), 1)

    def test_a_stuck_lock_is_infrastructure_not_a_replay(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "c.db"
            ledger = ConsumedIds(db)
            ledger.BUSY_TIMEOUT_S, ledger.MAX_ATTEMPTS = 0.05, 2
            holder = sqlite3.connect(db, isolation_level=None)
            holder.execute("BEGIN IMMEDIATE")
            try:
                with self.assertRaises(ConsumptionUnavailable) as ctx:
                    ledger.consume("approval:y")
                self.assertNotIsInstance(ctx.exception, AlreadyConsumedError)
            finally:
                holder.execute("ROLLBACK")
                holder.close()
            ledger.consume("approval:y")   # works once the lock clears


class TestColdRestart(unittest.TestCase):
    """Process A consumes and exits; process B, a fresh interpreter with no
    shared memory, is refused the same envelope by the same database file."""

    def test_process_b_is_refused_after_process_a_exits(self):
        with tempfile.TemporaryDirectory() as d:
            db = str(Path(d) / "consumed.db")
            env_file = Path(d) / "envelope.json"
            env_file.write_text(json.dumps(_signed_envelope_dict()))
            script = (
                "import json,sys; sys.path.insert(0, sys.argv[3]);"
                "from foundation.tests.test_ring0_boundary import _attempt;"
                "from foundation.approval_envelope import ConsumedIds;"
                "from pathlib import Path;"
                "r=_attempt(sys.argv[1], json.load(open(sys.argv[2])));"
                "print(f'{sys.argv[4]} pid={__import__(\"os\").getpid()} result={r} "
                "db_count={ConsumedIds(Path(sys.argv[1])).count(\"approval:ring0-nonce-1\")}')")
            child_env = dict(os.environ, **{RING0_SECRET_ENV: SECRET,
                                            "PYTHONDONTWRITEBYTECODE": "1"})
            outs = []
            for name in ("PROCESS_A", "PROCESS_B"):
                r = subprocess.run([sys.executable, "-c", script, db, str(env_file),
                                    str(REPO_ROOT), name],
                                   cwd=REPO_ROOT, env=child_env, capture_output=True,
                                   text=True, timeout=120)
                self.assertEqual(r.returncode, 0, r.stderr)
                outs.append(r.stdout.strip())
                print(outs[-1], file=sys.stderr)
        self.assertIn("result=SUCCESS db_count=1", outs[0])
        self.assertIn("result=ALREADY_CONSUMED db_count=1", outs[1])
        self.assertNotEqual(outs[0].split()[1], outs[1].split()[1])  # different pids


class TestMultiProcessRace(unittest.TestCase):
    """N separate processes, same approval, same database file, released
    together. Exactly one wins; the rest get the domain-level rejection."""

    def test_exactly_one_contender_wins(self):
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as d:
            db = str(Path(d) / "consumed.db")
            ConsumedIds(Path(db))   # create the schema before the race
            envelope = _signed_envelope_dict(nonce="race-nonce-1")
            barrier, results = ctx.Barrier(RACE_N), ctx.Queue()
            old = os.environ.get(RING0_SECRET_ENV)
            os.environ[RING0_SECRET_ENV] = SECRET   # inherited by spawned children
            try:
                procs = [ctx.Process(target=_race_worker,
                                     args=(db, envelope, barrier, results))
                         for _ in range(RACE_N)]
                for p in procs:
                    p.start()
                outcomes = [results.get(timeout=180) for _ in procs]
                for p in procs:
                    p.join(timeout=60)
            finally:
                if old is None:
                    os.environ.pop(RING0_SECRET_ENV, None)
                else:
                    os.environ[RING0_SECRET_ENV] = old
            final = ConsumedIds(Path(db)).count("approval:race-nonce-1")
        success = outcomes.count("SUCCESS")
        rejected = outcomes.count("ALREADY_CONSUMED")
        unexpected = [o for o in outcomes if o.startswith("UNEXPECTED")]
        print(f"RACE N={RACE_N}\nSUCCESS={success}\nALREADY_CONSUMED={rejected}\n"
              f"UNEXPECTED_ERRORS={len(unexpected)}\nFINAL_DB_CONSUMPTIONS={final}",
              file=sys.stderr)
        self.assertEqual(unexpected, [])
        self.assertEqual((success, rejected, final), (1, RACE_N - 1, 1))


class TestSingleChokepoint(unittest.TestCase):

    def test_public_dispatcher_routes_fail_closed(self):
        d = AdapterDispatcher.from_adapters([])
        for call in (lambda: d.execute(_intent()),
                     lambda: d.execute_approved_with_receipt(_intent(), "x", None)):
            with self.assertRaisesRegex(AdapterDispatchError, "not a public execution route"):
                call()

    def test_only_the_gateway_reaches_the_private_dispatcher(self):
        """AST scan of every production module: private dispatcher methods,
        adapter.execute and ExecutionPermit construction appear only where
        the boundary lives."""
        allowed = {
            "_execute": {"adapter_execution_gateway.py", "execution_dispatcher.py"},
            "_execute_approved_with_receipt": {"execution_dispatcher.py"},
            "_execute_adapter": {"execution_dispatcher.py"},
            "ExecutionPermit": {"authorization_gate.py"},
        }
        found = {k: set() for k in allowed}
        for path in (REPO_ROOT / "foundation").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                if name in found:
                    found[name].add(path.name)
                if (isinstance(f, ast.Attribute) and f.attr == "execute"
                        and isinstance(f.value, ast.Name) and f.value.id == "adapter"):
                    found.setdefault("adapter.execute", set()).add(path.name)
        for name, files in found.items():
            limit = allowed.get(name, {"execution_dispatcher.py"})
            self.assertTrue(files <= limit, f"{name} called from {sorted(files - limit)}")


if __name__ == "__main__":
    unittest.main()
