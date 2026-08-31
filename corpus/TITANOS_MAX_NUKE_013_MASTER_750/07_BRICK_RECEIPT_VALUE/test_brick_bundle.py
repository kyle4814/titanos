def test_brick_bundle_contract():
    from titanos_stub import validate_brick_bundle
    assert validate_brick_bundle({})["status"] == "PROPOSED"
