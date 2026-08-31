STEPS = (
    "LOAD","CENSUS","SEARCH","CLASSIFY","PARETO","QUEUE","ROUTE",
    "IMPLEMENT","TEST","BLUE_TEAM","RECEIPT","CHECKPOINT",
    "CALIBRATE","PERSIST","NEXT"
)

def validate_transition(current, nxt):
    if current not in STEPS or nxt not in STEPS:
        raise ValueError("unknown rail state")
    i = STEPS.index(current)
    j = STEPS.index(nxt)
    if j != i + 1:
        raise ValueError(f"non-sequential transition: {current}->{nxt}")
    return True
