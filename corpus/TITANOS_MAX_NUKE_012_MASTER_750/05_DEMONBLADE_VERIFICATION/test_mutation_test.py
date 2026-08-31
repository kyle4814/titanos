def test_mutation_test_contract():
    from titanos_stub import validate_mutation_test
    assert validate_mutation_test({})["status"] == "PROPOSED"
