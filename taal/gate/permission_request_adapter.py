"""
TAAL — permission_request -> GateInput adapter (`PARETO_FRONTIER.md`
FRONTIER-002).

WHAT THIS FILE IS

`taal/schema/permission_request.py` and `taal/gate/root_gate.py::
GateInput` were both built already, independently, deliberately
decoupled — `GateInput`'s own docstring says so explicitly: "Deliberately
NOT built against taal/schema/permission_request.py... a future
integration layer is responsible for mapping a validated
permission_request document onto a GateInput, not this file." This is
that integration layer. Neither source module is modified.

WHAT MAPS DIRECTLY

`request_id`/`requester`/`action`/`resource`/`scope`/`duration`/
`delegation` all correspond 1:1 by field name. `provenance_status` maps
directly too — both modules independently use the identical four-value
set (`VERIFIED`/`CLAIMED`/`UNKNOWN`/`UNVERIFIABLE`), verified by test
rather than assumed. `reversible` is derived: `reversibility ==
"FULLY_REVERSIBLE"` (permission_request's four-value enum collapses to
root_gate's boolean — `PARTIALLY_REVERSIBLE`/`IRREVERSIBLE`/`UNKNOWN` all
map to `False`, the conservative direction). `high_impact` is derived:
`True` if `action` is in `permission_request.HIGH_STAKES_ACTIONS` OR
`reversibility == "IRREVERSIBLE"` — either signal alone is enough to flag
it, matching root_gate's own "this can only make the verdict more
conservative" ratchet philosophy (`_cap`).

WHAT DELIBERATELY DOES NOT MAP — AND WHY THIS IS THE ACTUAL SEAM

`GateInput.identity_verified`, `.authority_asserted`,
`.authority_evidence`, `.scope_declared_necessary`, `.reducible_scope`,
`.supporting_evidence`, `.contradictory_evidence` have NO corresponding
field anywhere in `permission_request`'s schema, and this is not an
oversight to fix — it is the same self-certification boundary
`permission_request.py`'s own docstring names as the load-bearing
property of that schema (`self_authorized` always fails PR-R-9,
`risk_hint` is never authoritative). A permission_request document is
the ASK; it structurally cannot also assert "and my identity is
verified" or "and my authority claim has evidence" about itself — those
facts must come from an independent identity/authority-verification
step this adapter has no access to and must not fabricate. Every one of
these fields is left at `GateInput`'s own fail-closed default
(`False`/`()`), never derived from the request document, on every call.
This is the actual thing FRONTIER-002 needed proven, not just the
mechanical field renaming.
"""

from __future__ import annotations

from typing import Any, Mapping

from taal.gate.root_gate import GateInput
from taal.schema.permission_request import HIGH_STAKES_ACTIONS

__all__ = ["permission_request_to_gate_input"]


def permission_request_to_gate_input(pr: Mapping[str, Any]) -> GateInput:
    """Map an already-validated `permission_request` mapping (the dict
    under the `permission_request:` top-level key — e.g.
    `yaml.safe_load(text)["permission_request"]` after
    `validate_permission_request()` has passed it) onto a `GateInput`.

    Does not itself validate `pr` — callers are expected to have run
    `taal.validators.validate_permission_request.validate_permission_
    request()` first, exactly as every other consumer of a validated
    document in this repository does (schema validation and gate
    evaluation remain two separate steps, never merged).
    """
    reversibility = pr.get("reversibility")
    action = pr.get("action")

    return GateInput(
        request_id=pr.get("id", ""),
        requester=pr.get("requester", ""),
        action=action or "",
        resource=pr.get("resource", ""),
        scope=pr.get("scope", ""),
        duration=pr.get("duration", ""),
        delegation=bool(pr.get("delegation", False)),
        reversible=(reversibility == "FULLY_REVERSIBLE"),
        provenance_status=pr.get("provenance", "UNKNOWN"),
        high_impact=(
            action in HIGH_STAKES_ACTIONS or reversibility == "IRREVERSIBLE"
        ),
        # Deliberately NOT derived from `pr` — see module docstring.
        # identity_verified / authority_asserted / authority_evidence /
        # scope_declared_necessary / reducible_scope / supporting_evidence
        # / contradictory_evidence all stay at GateInput's own fail-closed
        # defaults.
    )
