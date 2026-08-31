"""TitanOS bounded scaffold: partner_payout."""
def validate_partner_payout(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"partner_payout"}
