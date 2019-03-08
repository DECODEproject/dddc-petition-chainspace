from scripts.zencontract import ZenContract, CONTRACTS
import json

def print_json(label, json_str):
    formatted = json.dumps(json.loads(json_str), sort_keys=True, indent=4)
    print(label + ":\n" + formatted)

def execute_contract(contractName, keys=None, data=None):
    contract = ZenContract(contractName)
    contract.keys(keys)
    contract.data(data)
    result = contract.execute()
    if (result != None) and result.startswith("{"):
        print_json(contractName, result)
    else:
        print(contractName + ":\n" + result)
    return result


citizen_keypair = execute_contract(CONTRACTS.CITIZEN_KEYGEN)
credential_issuer_keypair = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_GENERATE_KEYPAIR)
credential_issuer_verification_keypair = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_PUBLISH_VERIFY, keys=credential_issuer_keypair)

citizen_credential_request = execute_contract(CONTRACTS.CITIZEN_CREDENTIAL_REQUEST, keys=citizen_keypair)

credential_issuer_signed_credential = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_SIGN_CREDENTIAL,
                                        keys=credential_issuer_keypair,
                                        data=citizen_credential_request)

credential = execute_contract(CONTRACTS.CITIZEN_AGGREGATE_CREDENTIAL,
                              keys=citizen_keypair,
                              data=credential_issuer_signed_credential)

# How come the citizen needs the verification keypair of the credential issuer? surely only needs the public key?
# Also why is the data and the keys appear to be swapped around on this one?
credential_proof = execute_contract(CONTRACTS.CITIZEN_PROVE_CREDENTIAL,
                                    keys=credential,
                                    data=credential_issuer_verification_keypair)


verification_result = execute_contract(CONTRACTS.VERIFIER_VERIFY_CREDENTIAL,
                                       keys=credential_proof,
                                       data=credential_issuer_verification_keypair)

assert verification_result == "OK"

citizen_create_petition_request = execute_contract(CONTRACTS.CITIZEN_CREATE_PETITION,
                                            keys=credential,
                                            data=credential_issuer_verification_keypair)

citizen_petition = execute_contract(CONTRACTS.VERIFIER_APPROVE_PETITION,
                            keys=credential_issuer_verification_keypair,
                            data=citizen_create_petition_request)

citizen_petition_signature = execute_contract(CONTRACTS.CITIZEN_SIGN_PETITION,
                                      keys=credential,
                                      data=credential_issuer_verification_keypair)

petition_with_signature = execute_contract(CONTRACTS.LEDGER_INCREMENT_PETITION,
                                           keys=citizen_petition,
                                           data=citizen_petition_signature)

citizen_tally = execute_contract(CONTRACTS.CITIZEN_TALLY_PETITION,
                                 keys=credential,
                                 data=petition_with_signature)

tally_count = execute_contract(CONTRACTS.CITIZEN_COUNT_PETITION,
                               keys=citizen_tally,
                               data=petition_with_signature)

