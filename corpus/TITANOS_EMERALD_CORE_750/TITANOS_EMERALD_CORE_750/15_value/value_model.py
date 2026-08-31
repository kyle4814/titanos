STATES = ("MODELLED","OBSERVED","VERIFIED","REALIZED")
def valid_state(state):
    return state in STATES
def can_upgrade(old, new):
    return STATES.index(new) >= STATES.index(old)
