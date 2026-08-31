"""
Tests for foundation/write_scope.py — the write-scope enforcement
primitive built after the real incident (see module docstring): a
subagent given a write scope as a PROMPT INSTRUCTION ran `git stash` and
destroyed ~1,000 lines of another worker's concurrent uncommitted work.
These tests attack path traversal hardest, per that module's own
"this is the part most likely to be got wrong" note.
"""

import os
import tempfile
import unittest
from pathlib import Path

from foundation.write_scope import (
    FORBIDDEN_OPERATIONS,
    WriteScope,
    WriteScopeViolation,
    authorize_operation,
    authorize_write,
    scoped_writer,
)
from foundation import write_scope as _module


def _scope(allowed_paths=("foundation/tests/*.py",), **overrides) -> WriteScope:
    base = dict(
        task_id="T-001",
        actor="test-agent",
        allowed_paths=allowed_paths,
        reason="unit test",
    )
    base.update(overrides)
    return WriteScope(**base)


class TestWriteInsideScope(unittest.TestCase):
    def test_path_inside_scope_is_allowed(self):
        scope = _scope(allowed_paths=("foundation/write_scope.py",))
        self.assertTrue(authorize_write(scope, "foundation/write_scope.py"))

    def test_glob_matches_sibling_files(self):
        scope = _scope(allowed_paths=("foundation/tests/*.py",))
        self.assertTrue(
            authorize_write(scope, "foundation/tests/test_write_scope.py")
        )

    def test_recursive_glob_matches_nested_path(self):
        scope = _scope(allowed_paths=("foundation/*",))
        self.assertTrue(
            authorize_write(scope, "foundation/tests/test_write_scope.py")
        )


class TestWriteOutsideScopeRaises(unittest.TestCase):
    def test_path_outside_scope_raises(self):
        scope = _scope(allowed_paths=("foundation/tests/*.py",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "kpm/source-vault/registry.py")

    def test_violation_message_names_actor_and_path(self):
        scope = _scope(
            actor="rogue-subagent",
            allowed_paths=("foundation/tests/*.py",),
        )
        with self.assertRaises(WriteScopeViolation) as ctx:
            authorize_write(scope, "kpm/some_file.py")
        message = str(ctx.exception)
        self.assertIn("rogue-subagent", message)
        self.assertIn("kpm/some_file.py", message)

    def test_authorize_write_raises_not_returns_false(self):
        """The exact discipline this module borrows from
        communication_gate.py / publication_gate.py: assert the raised
        TYPE, not merely a falsy return — a caller that only checks
        `if authorize_write(...):` without a try/except must be unable
        to silently proceed on denial."""
        scope = _scope(allowed_paths=("foundation/tests/*.py",))
        with self.assertRaises(WriteScopeViolation):
            result = authorize_write(scope, "somewhere/else.py")
            # If this line were ever reached, it would prove the
            # function returned instead of raising.
            self.assertFalse(result)


class TestEmptyAllowedPathsFailsClosed(unittest.TestCase):
    def test_empty_allowed_paths_permits_nothing(self):
        scope = _scope(allowed_paths=())
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "foundation/write_scope.py")

    def test_empty_allowed_paths_refuses_even_repo_root(self):
        scope = _scope(allowed_paths=())
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, ".")


class TestPathTraversalIsRefused(unittest.TestCase):
    """The central threat this module exists to defeat. Naive string
    matching (e.g. str.startswith) would be fooled by several of these;
    resolved-path containment must not be."""

    def test_dotdot_traversal_refused(self):
        scope = _scope(allowed_paths=("foundation/*",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "foundation/../../etc/passwd")

    def test_absolute_path_outside_repo_refused(self):
        scope = _scope(allowed_paths=("foundation/*",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "/etc/passwd")

    def test_absolute_path_inside_repo_still_requires_glob_match(self):
        repo_root = _module._repo_root()
        scope = _scope(allowed_paths=("foundation/tests/*.py",))
        outside_path = str(repo_root / "kpm" / "somewhere.py")
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, outside_path)

    def test_prefix_collision_directory_refused(self):
        """foundation_evil/x.py shares a string PREFIX with an
        allowance of foundation/ but must not be permitted — this is
        the exact case naive str.startswith("foundation") would get
        wrong."""
        scope = _scope(allowed_paths=("foundation/*",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "foundation_evil/x.py")

    def test_prefix_collision_reverse_direction_also_refused(self):
        scope = _scope(allowed_paths=("foundation_evil/*",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(scope, "foundation/write_scope.py")

    def test_symlink_pointing_outside_repo_refused(self):
        repo_root = _module._repo_root()
        with tempfile.TemporaryDirectory() as outside_dir:
            outside_target = Path(outside_dir) / "secret.txt"
            outside_target.write_text("outside the repo")

            link_dir = repo_root / "foundation" / "tests"
            link_path = link_dir / "_tmp_traversal_symlink.py"
            try:
                os.symlink(outside_target, link_path)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not supported on this platform")

            try:
                scope = _scope(allowed_paths=("foundation/tests/*.py",))
                with self.assertRaises(WriteScopeViolation):
                    authorize_write(
                        scope, "foundation/tests/_tmp_traversal_symlink.py"
                    )
            finally:
                link_path.unlink(missing_ok=True)

    def test_deep_dotdot_chain_refused(self):
        scope = _scope(allowed_paths=("foundation/tests/*.py",))
        with self.assertRaises(WriteScopeViolation):
            authorize_write(
                scope,
                "foundation/tests/../../../../../../../../etc/shadow",
            )


class TestForbiddenOperationsAreUnconditional(unittest.TestCase):
    """No allowed_paths configuration, however permissive, may
    authorize an operation in FORBIDDEN_OPERATIONS."""

    def _maximally_permissive_scope(self) -> WriteScope:
        return _scope(allowed_paths=("*", "**/*", "*/*"))

    def test_every_forbidden_operation_is_refused(self):
        scope = self._maximally_permissive_scope()
        for op in FORBIDDEN_OPERATIONS:
            with self.assertRaises(WriteScopeViolation, msg=op):
                authorize_operation(scope, op)

    def test_git_stash_specifically_refused_named_after_real_incident(self):
        """git stash is the exact operation that destroyed ~1,000 lines
        of concurrent uncommitted work in this project's real incident
        (see write_scope.py's module docstring). This must never be
        authorizable, under any scope."""
        scope = self._maximally_permissive_scope()
        with self.assertRaises(WriteScopeViolation) as ctx:
            authorize_operation(scope, "git stash")
        self.assertIn("stash", str(ctx.exception).lower())

    def test_git_stash_with_arguments_also_refused(self):
        scope = self._maximally_permissive_scope()
        with self.assertRaises(WriteScopeViolation):
            authorize_operation(scope, "git stash pop")

    def test_dot_git_write_refused(self):
        scope = self._maximally_permissive_scope()
        with self.assertRaises(WriteScopeViolation):
            authorize_operation(scope, ".git/write")

    def test_non_forbidden_operation_permitted(self):
        scope = self._maximally_permissive_scope()
        self.assertTrue(authorize_operation(scope, "write foundation/x.py"))

    def test_empty_operation_refused_fail_closed(self):
        scope = self._maximally_permissive_scope()
        with self.assertRaises(WriteScopeViolation):
            authorize_operation(scope, "")


class TestScopedWriter(unittest.TestCase):
    def test_scoped_writer_writes_within_scope(self):
        repo_root = _module._repo_root()
        rel_path = "foundation/tests/_tmp_scoped_writer_output.txt"
        scope = _scope(allowed_paths=("foundation/tests/*.txt",))
        write = scoped_writer(scope)
        try:
            write(rel_path, "hello")
            self.assertEqual((repo_root / rel_path).read_text(), "hello")
        finally:
            (repo_root / rel_path).unlink(missing_ok=True)

    def test_scoped_writer_refuses_out_of_scope_without_touching_disk(self):
        repo_root = _module._repo_root()
        rel_path = "kpm/_tmp_should_never_exist.txt"
        target = repo_root / rel_path
        scope = _scope(allowed_paths=("foundation/tests/*.txt",))
        write = scoped_writer(scope)
        try:
            with self.assertRaises(WriteScopeViolation):
                write(rel_path, "should not be written")
            self.assertFalse(target.exists())
        finally:
            if target.exists():
                target.unlink()


if __name__ == "__main__":
    unittest.main()
