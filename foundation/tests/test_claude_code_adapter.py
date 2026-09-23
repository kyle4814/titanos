from __future__ import annotations
import unittest
from foundation.claude_code_adapter import build_invocation
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.workforce_dispatcher import DispatchItem

class TestClaudeCodeAdapter(unittest.TestCase):
    def test_builds_bounded_invocation(self):
        c=WorkerExecutionContract("w1","o1","research",allowed_tools=("browser",),allowed_actions=("research",),forbidden_actions=("submit",),required_evidence=("url",),authority_ceiling="O1")
        i=build_invocation(DispatchItem("w1","research",0),c)
        self.assertIn("FORBIDDEN ACTIONS: submit",i.prompt)
        self.assertIn("AUTHORITY CEILING: O1",i.prompt)
        self.assertEqual(i.tools,("browser",))
    def test_rejects_mismatched_worker(self):
        c=WorkerExecutionContract("w1","o1","research")
        with self.assertRaises(ValueError): build_invocation(DispatchItem("w2","research",0),c)

if __name__=="__main__": unittest.main()
