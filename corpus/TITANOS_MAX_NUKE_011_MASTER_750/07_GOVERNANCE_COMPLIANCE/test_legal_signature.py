def test_legal_signature_contract():
    from titanos_stub import execute_legal_signature
    assert execute_legal_signature(None).status == "REJECT"
    assert execute_legal_signature({}).status == "PROPOSED"
