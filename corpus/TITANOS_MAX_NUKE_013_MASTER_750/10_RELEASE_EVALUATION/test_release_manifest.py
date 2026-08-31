def test_release_manifest_contract():
    from titanos_stub import validate_release_manifest
    assert validate_release_manifest({})["status"] == "PROPOSED"
