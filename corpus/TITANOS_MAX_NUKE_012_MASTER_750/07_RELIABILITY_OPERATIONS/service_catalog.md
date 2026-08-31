def test_service_catalog_contract():
    from titanos_stub import validate_service_catalog
    assert validate_service_catalog({})["status"] == "PROPOSED"
