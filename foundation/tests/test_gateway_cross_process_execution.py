"""Exactly-once adapter execution per fingerprint ACROSS PROCESSES.

`AdapterExecutionGateway.execute_permitted` serialised check-existing /
execute / persist under the dispatcher's thread lock only. Two processes,
each holding its own valid permit for the same intent, could both observe
"no receipt yet" and both run the adapter (reproduced 2026-09-26: 4
processes -> 4 executions, 1 receipt, 3 "identity collision" errors after
the fact). The gateway now claims `exec:<fingerprint>` in the SQLite
ConsumedIds ledger -- the cross-process single-use primitive it already
holds -- before executing. The loser returns the authentic receipt if the
winner has persisted it, or raises ExecutionClaimed, fail closed; it never
executes.
"""
import multiprocessing as mp
import tempfile
import time
import unittest
from pathlib import Path

from foundation.adapter_execution_gateway import AdapterExecutionGateway, ExecutionClaimed
from foundation.approval_envelope import ApprovalEnvelope, ConsumedIds
from foundation.authorization_gate import AuthorizationGate, ExecutionPermit
from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatcher
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_receipt_store import ExecutionReceiptStore

KEY = b"k" * 32


def _intent():
    return ExecutionIntent(
        intent_id="EI-XPROC", target="stripe:customer_1", action="CREATE_PAYMENT_LINK",
        parameters={"amount": 1000, "currency": "AUD"}, evidence_refs=("OPP-1",),
        expected_effect="create one payment link", authority_required="A3", reversible=True,
        expires_at="2099-01-01T00:00:00+00:00", policy_version="mothership-1",
    )


class TallyAdapter:
    """Counts executions in a file so separate processes can be tallied."""
    name = "stripe"

    def __init__(self, tally_path, delay=0.0):
        self.tally_path, self.delay = tally_path, delay
        self.calls = 0

    def supports(self, intent):
        return intent.target.startswith("stripe:")

    def execute(self, intent):
        self.calls += 1
        with open(self.tally_path, "a") as f:
            f.write("EXEC\n")
        time.sleep(self.delay)
        return AdapterResult(status="EXECUTED", effect="payment link created",
                             executed=True, evidence=("stripe:receipt:123",))


def _permit(consumed, nonce):
    env = ApprovalEnvelope.decide(proposal_id="p", intent=_intent(), decision="APPROVE",
                                  authority="A3", reviewer="kyle", nonce=nonce).signed(KEY)
    return AuthorizationGate.issue(_intent(), env, key=KEY, consumed=consumed)


def _gateway(td, delay=0.0):
    adapter = TallyAdapter(f"{td}/tally", delay)
    return adapter, AdapterExecutionGateway(
        AdapterDispatcher.from_adapters([adapter]),
        ExecutionReceiptStore(f"{td}/receipts.json"), KEY, ConsumedIds(Path(td) / "consumed.db"))


def _process_worker(td, permit_dict, barrier, q):
    _, gw = _gateway(td, delay=0.15)
    barrier.wait()
    try:
        r = gw.execute_permitted(_intent(), ExecutionPermit(**permit_dict))
        q.put(("RECEIPT", r.receipt_id))
    except ExecutionClaimed as exc:
        q.put(("CLAIMED", str(exc)[:60]))
    except Exception as exc:  # noqa: BLE001 -- surfaced by the assertion below
        q.put((type(exc).__name__, str(exc)[:60]))


class CrossProcessExecutionTests(unittest.TestCase):
    def test_four_processes_one_fingerprint_execute_exactly_once(self):
        with tempfile.TemporaryDirectory() as td:
            consumed = ConsumedIds(Path(td) / "consumed.db")
            permits = [_permit(consumed, f"n{i}").to_dict() for i in range(4)]
            ctx = mp.get_context("spawn")
            q, barrier = ctx.Queue(), ctx.Barrier(4)
            procs = [ctx.Process(target=_process_worker, args=(td, p, barrier, q)) for p in permits]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            results = [q.get() for _ in procs]
            kinds = sorted(k for k, _ in results)
            executions = Path(td, "tally").read_text().count("EXEC")
            store = ExecutionReceiptStore(f"{td}/receipts.json").load()

            self.assertEqual(executions, 1, results)
            self.assertEqual(len(store), 1)
            self.assertTrue(all(k in ("RECEIPT", "CLAIMED") for k in kinds), results)
            self.assertGreaterEqual(kinds.count("RECEIPT"), 1)
            fp = _intent().fingerprint()
            for k, v in results:
                if k == "RECEIPT":
                    self.assertEqual(v, f"exec:{fp}")
            # The one persisted receipt is authentic and is the winner's.
            store[f"exec:{fp}"].verify(KEY, fp)
            # Cross-process claim is durable in the ledger.
            self.assertIn(f"exec:{fp}", consumed)

    def test_claim_held_elsewhere_with_no_receipt_fails_closed_without_executing(self):
        # Models: another process claimed the execution and has not persisted
        # its receipt yet (or crashed after claiming). We must not run the
        # adapter a second time; state is unknown, so refuse.
        with tempfile.TemporaryDirectory() as td:
            adapter, gw = _gateway(td)
            fp = _intent().fingerprint()
            gw.consumed.consume(f"exec:{fp}")
            with self.assertRaises(ExecutionClaimed):
                gw.execute_permitted(_intent(), _permit(gw.consumed, "n0"))
            self.assertEqual(adapter.calls, 0)
            self.assertFalse(Path(td, "receipts.json").exists())

    def test_claim_held_elsewhere_with_authentic_receipt_returns_it(self):
        with tempfile.TemporaryDirectory() as td:
            adapter, gw = _gateway(td)
            fp = _intent().fingerprint()
            gw.consumed.consume(f"exec:{fp}")
            winner = ExecutionReceipt(
                receipt_id=f"exec:{fp}", intent_id="EI-XPROC", fingerprint=fp,
                target="stripe:customer_1", action="CREATE_PAYMENT_LINK", status="EXECUTED",
                executed=True, recorded_at="2026-09-26T00:00:00+00:00", evidence="stripe:receipt:123",
            ).sign(KEY)
            gw.receipt_store.record(winner)
            got = gw.execute_permitted(_intent(), _permit(gw.consumed, "n0"))
            self.assertEqual(got, winner)
            self.assertEqual(adapter.calls, 0)

    def test_sequential_calls_still_idempotent_and_claim_once(self):
        with tempfile.TemporaryDirectory() as td:
            adapter, gw = _gateway(td)
            first = gw.execute_permitted(_intent(), _permit(gw.consumed, "n0"))
            second = gw.execute_permitted(_intent(), _permit(gw.consumed, "n1"))
            self.assertEqual(first, second)
            self.assertEqual(adapter.calls, 1)
            fp = _intent().fingerprint()
            self.assertEqual(gw.consumed.count(f"exec:{fp}"), 1)

    def test_same_permit_replay_is_still_refused_before_any_claim(self):
        from foundation.authorization_gate import ApprovalReplayed
        with tempfile.TemporaryDirectory() as td:
            adapter, gw = _gateway(td)
            permit = _permit(gw.consumed, "n0")
            gw.execute_permitted(_intent(), permit)
            with self.assertRaises(ApprovalReplayed):
                gw.execute_permitted(_intent(), permit)
            self.assertEqual(adapter.calls, 1)


if __name__ == "__main__":
    unittest.main()
