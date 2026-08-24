# Security

## Static scan for dangerous surfaces (§Phase 7)

```
grep -rnE '\b(delete|purge|clear|remove|overwrite|force|bypass|override|
            unsafe|skip_validation|disable_validation)\b' --include='*.py' .
```

Run 2026-08-25 against `schema/`, `firewall/`, `legacy/`. Every hit
classified:

| File:line | Context | Classification |
|---|---|---|
| `schema/validator.py:26` | docstring, describes what content CANNOT do | documentation of prohibition |
| `schema/validator.py:421` | `_forbidden_keys` literal set (`skip_validation`, `disable_validation`, ...) | these strings exist ONLY to be detected and rejected (R-11) — not callable methods |
| `firewall/dissent.py:82` | docstring: "No delete surface" | documentation of absence |
| `firewall/quarantine.py:80,111,114` | docstring: "no `delete`... property being demonstrated" | documentation of absence |
| `legacy/classify.py:6` | docstring: "no write, no rename, no delete" | documentation of prohibition |

**Result: zero live dangerous methods found anywhere in the scanned tree.**
Every occurrence of these words is either a comment describing an absence,
or a string literal in a rejection list. **VERIFIED, by the grep output
itself — reproducible by anyone.**

## Never execute artifact content

No module under `schema/` or `firewall/` calls `eval`, `exec`, `import`,
`__import__`, `subprocess`, or any dynamic-code-from-string mechanism on
artifact content. `schema/validator.py` uses `yaml.SafeLoader` exclusively
(never `yaml.Loader`/`FullLoader`, which permit arbitrary Python object
construction from tags). **VERIFIED PROPERTY**, now enforced by a
permanent AST scan ported from `titanos-provenance/tests/test_no_network.py`
— `schema/tests/test_no_network.py` (3/3), covering `schema/`, `firewall/`,
`legacy/`.

## Fail-closed on internal error

`validate_artifact()`'s outer try/except (R-0) means an unforeseen
exception becomes a loud `INVALID`, never a silent pass. See
`VALIDATION.md`. This is the single most important security property in
this codebase, because every other rule depends on the function actually
returning a verdict instead of crashing past the caller's error handling.

## Known unresolved security gaps

1. No cryptographic signature verification (shape-only, see THREAT_MODEL.md).
2. No independent second-reviewer requirement for quarantine release (see
   `POLE_REVERSAL_DOCTRINE.yaml` PR-I-04).
3. `reviewed_by` is an unauthenticated free-text field (PR-I-05).
