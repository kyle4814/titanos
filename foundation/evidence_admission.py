"""Normalize source observations into provenance-bound evidence candidates."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class EvidenceCandidate:
    source_id: str
    source_url: str
    observed_at: str
    payload: object
    fingerprint: str


def normalize_observation(
    source_id: str,
    observation: object,
    *,
    source_url: str,
    observed_at: str,
) -> EvidenceCandidate:
    if not source_id.strip() or not source_url.strip() or not observed_at.strip():
        raise ValueError("source_id, source_url and observed_at are required")
    canonical = json.dumps(observation, sort_keys=True, separators=(",", ":"), default=str)
    fingerprint = "sha256:" + sha256(
        f"{source_id}\n{source_url}\n{observed_at}\n{canonical}".encode()
    ).hexdigest()
    return EvidenceCandidate(source_id, source_url, observed_at, observation, fingerprint)


def admit_evidence(candidate: EvidenceCandidate) -> EvidenceCandidate:
    if not candidate.source_id or not candidate.source_url or not candidate.fingerprint.startswith("sha256:"):
        raise ValueError("evidence candidate lacks provenance or integrity")
    return candidate


__all__ = ["EvidenceCandidate", "normalize_observation", "admit_evidence"]
