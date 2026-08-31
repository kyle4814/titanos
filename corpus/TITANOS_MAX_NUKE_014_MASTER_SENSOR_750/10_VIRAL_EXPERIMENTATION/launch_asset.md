def test_launch_asset_contract():
    from titanos_stub import observe_launch_asset
    assert observe_launch_asset({})["status"] == "OBSERVED"
