def test_deployment_backup_contract():
    from titanos_stub import validate_deployment_backup
    assert validate_deployment_backup({})["status"] == "PROPOSED"
