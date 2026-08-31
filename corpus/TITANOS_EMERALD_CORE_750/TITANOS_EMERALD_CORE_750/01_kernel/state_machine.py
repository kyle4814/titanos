VALID = {
    "QUEUED": {"CLAIMED"},
    "CLAIMED": {"RUNNING", "QUEUED"},
    "RUNNING": {"VERIFYING", "FAILED", "BLOCKED"},
    "VERIFYING": {"BLUE_TEAM", "FAILED"},
    "BLUE_TEAM": {"CHECKPOINTING", "FAILED"},
    "CHECKPOINTING": {"COMPLETE", "FAILED"},
    "COMPLETE": set(),
    "BLOCKED": {"QUEUED"},
    "FAILED": {"QUEUED", "ROLLED_BACK"},
    "ROLLED_BACK": {"QUEUED"},
}
def transition(current, target):
    if target not in VALID.get(current, set()):
        raise ValueError(f"invalid transition: {current} -> {target}")
    return target
