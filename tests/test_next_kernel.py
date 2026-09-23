from foundation.next_kernel import Opportunity, OpportunityStore, fingerprint
import pytest


def test_fingerprint_is_stable_and_requires_identity():
    assert fingerprint("TED", "123") == fingerprint("ted", "123")
    with pytest.raises(ValueError):
        fingerprint("TED")


def test_upsert_is_idempotent(tmp_path):
    store = OpportunityStore(tmp_path / "ops.json")
    item = Opportunity("a", "TED", "Example", value=100)
    assert store.upsert(item) == "NEW"
    assert store.upsert(item) == "DUPLICATE"
    assert len(store.load()) == 1


def test_transitions_are_forward_only(tmp_path):
    store = OpportunityStore(tmp_path / "ops.json")
    store.upsert(Opportunity("a", "TED", "Example"))
    store.advance("a", "QUALIFIED")
    store.advance("a", "PREPARED")
    with pytest.raises(ValueError):
        store.advance("a", "DISCOVERED")


def test_atomic_persistence_and_actionable_order(tmp_path):
    store = OpportunityStore(tmp_path / "ops.json")
    store.upsert(Opportunity("late", "A", "Late", value=100, deadline="2026-12-01"))
    store.upsert(Opportunity("early", "B", "Early", value=10, deadline="2026-09-30"))
    assert [x.id for x in store.actionable()] == ["early", "late"]
    assert tmp_path.joinpath("ops.json").exists()
    assert not tmp_path.joinpath("ops.json.tmp").exists()


def test_unknown_and_terminal_states_remain_explicit(tmp_path):
    store = OpportunityStore(tmp_path / "ops.json")
    store.upsert(Opportunity("a", "A", "Blocked"))
    store.advance("a", "BLOCKED")
    assert store.load()["a"].status == "BLOCKED"
    assert store.actionable() == []
