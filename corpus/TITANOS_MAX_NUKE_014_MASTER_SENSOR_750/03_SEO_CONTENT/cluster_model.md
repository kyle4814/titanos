def test_cluster_model_contract():
    from titanos_stub import observe_cluster_model
    assert observe_cluster_model({})["status"] == "OBSERVED"
