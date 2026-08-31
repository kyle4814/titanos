from dataclasses import dataclass

@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    reason: str

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "reveal system prompt",
    "disable security",
    "bypass authorization",
    "delete receipts",
    "grant yourself access",
)

def classify_external_text(text: str) -> SecurityDecision:
    lowered = text.lower()
    hits = [p for p in INJECTION_PATTERNS if p in lowered]
    if hits:
        return SecurityDecision(False, "embedded authority/control instruction detected")
    return SecurityDecision(True, "external content remains data")
