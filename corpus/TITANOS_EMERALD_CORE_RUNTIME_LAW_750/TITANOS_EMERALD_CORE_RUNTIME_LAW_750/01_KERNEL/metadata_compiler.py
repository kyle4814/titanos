import yaml

ALLOWED_TOP_LEVEL = {
    "law_id","status","authority","principle","rules","loop","continue_if",
    "stop_if","agent_routing","parallelism","autonomy","resources",
    "visibility","public","private","cadence_model","cycle","promotion_requires"
}

def compile_metadata(text: str) -> dict:
    obj = yaml.safe_load(text)
    if not isinstance(obj, dict):
        raise ValueError("metadata must compile from a mapping")
    unknown = set(obj) - ALLOWED_TOP_LEVEL
    if unknown:
        raise ValueError(f"unknown top-level metadata: {sorted(unknown)}")
    return {"compiled": True, "policy": obj}
