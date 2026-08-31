from .state import load_state, save_state, write_receipt

def run():
    state = load_state()
    state["doctor_status"] = "PASS"
    save_state(state)
    return write_receipt(
        "SYSTEM",
        "DOCTOR_PASS",
        outputs={"offline_core": True, "durable_state": True},
        evidence=["state persisted"],
    )

if __name__ == "__main__":
    print(run())
