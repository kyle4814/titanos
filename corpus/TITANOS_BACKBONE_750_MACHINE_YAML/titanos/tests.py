from .core import enqueue, pareto, sha256_text

def test_hash():
    assert sha256_text("titanos") == sha256_text("titanos")

def test_pareto():
    tasks = [{"task_id":"b","priority":1},{"task_id":"a","priority":2}]
    assert pareto(tasks)[0]["task_id"] == "a"

def test_enqueue():
    t = enqueue("health", 100)
    assert t.status == "QUEUED"
