from scripts.zencontract import ZenContract, CONTRACTS


def test_zencontract():
    smart_contract = ZenContract(CONTRACTS.GENERATE_KEYPAIR)
    assert smart_contract
    assert not smart_contract.data()
    assert not smart_contract.keys()


def test_data():
    smart_contract = ZenContract(CONTRACTS.GENERATE_KEYPAIR)
    smart_contract.data("test")

    assert smart_contract.data() == "test"


def test_keys():
    smart_contract = ZenContract(CONTRACTS.GENERATE_KEYPAIR)
    smart_contract.keys("test")

    assert smart_contract.keys() == "test"


def _smart_contract_check(smart_contract, expected):
    result = smart_contract.execute()
    print(result)
    assert result, smart_contract.errors()
    for _ in expected:
        assert _ in result, smart_contract.errors()


def test_execute():
    expected = ["encoding", "x", "zenroom", "sign", "schema", "curve"]
    contract = ZenContract(CONTRACTS.GENERATE_KEYPAIR)
    _smart_contract_check(contract, expected)


def test_issuer_public():
    expected = "issuer_identifier verify beta alpha".split()
    contract = ZenContract(CONTRACTS.PUBLIC_VERIFY)
    contract.keys(ZenContract(CONTRACTS.GENERATE_KEYPAIR).execute())
    _smart_contract_check(contract, expected)


def test_keygen():
    expected = "identifier public private".split()
    contract = ZenContract(CONTRACTS.CITIZEN_KEYGEN)
    _smart_contract_check(contract, expected)


def test_request():
    keys = ZenContract(CONTRACTS.CITIZEN_KEYGEN).execute()
    expected = "request pi_s rk rr cm public".split()
    contract = ZenContract(CONTRACTS.CITIZEN_REQ_BLIND_SIG)
    contract.keys(keys)
    _smart_contract_check(contract, expected)
