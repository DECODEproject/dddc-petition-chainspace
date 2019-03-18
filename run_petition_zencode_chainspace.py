# system
import requests
import json
import pprint
from datetime import datetime

# chainspace
import chainspacecontract as csc

# petitions contracts
from scripts import petition_zenroom as petition
from scripts.petition_zenroom import contract as petition_contract

from scripts.zencontract import ZenContract, CONTRACTS
import json


debug = 1
debug_zen = 0

pp = pprint.PrettyPrinter(indent=4)


def print_json(label, json_str):
    formatted = json.dumps(json.loads(json_str), sort_keys=True, indent=4)
    print(label + ":\n" + formatted)


def execute_contract(contractName, keys=None, data=None):
    contract = ZenContract(contractName)
    contract.keys(keys)
    contract.data(data)
    res = contract.execute()
    if debug_zen is 1:
        if (res is not None) and res.startswith("{"):
            print_json(contractName, res)
        else:
            print(contractName + ":\n" + res)
    return res


def pp_json(json_str):
    pp_object(json.loads(json_str))


def pp_object(obj):
    pp.pprint(obj)


def debug_cs_object(cs_obj_str):
    cs_obj = json.loads(cs_obj_str)
    print("\nCHAINSPACE OBJECT:" + "(" + cs_obj['type'] + ")")
    pp_object(cs_obj)


def debug_list_of_cs_object(list_of_json_str):
    for json_str in list_of_json_str:
        debug_cs_object(json_str)


def debug_tx(tx):
    print("\nCHAINSPACE TX (" + tx['contractID'] + "." + tx['methodID'] + ")  ==================")
    print("dependencies     : " + str(tx['dependencies']))
    print("parameters       : " + str(tx['parameters']))
    print("referenceInputs  : " + str(tx['referenceInputs']))
    print("returns          : " + str(tx['returns']))
    print("\ninputs         :")
    debug_list_of_cs_object(tx['inputs'])
    print("\noutputs        :")
    debug_list_of_cs_object(tx['outputs'])
    print("END TX  =============================================================================\n")


results = []


def post_transaction(transaction, path):
    tx = csc.transaction_inline_objects(transaction)
    print("\nPosting transaction to " + path)
    if debug == 1:
        debug_tx(tx)

    start_tx = datetime.now()
    response = requests.post(
        'http://127.0.0.1:5000/'
        + petition_contract.contract_name
        + path,
        json=tx)

    client_latency = (datetime.now() - start_tx)
    print(response.text)
    if response.text.startswith("{"):
        json_response = json.loads(response.text)
        results.append((json_response['success'], response.url, str(client_latency), transaction['transaction']['methodID']))
    else:
        print(response.text)
        results.append((False, response.url, str(client_latency, transaction['transaction']['methodID'])))

    return response


print("Petition Setup:")
petition_UUID = 1234  # petition unique id (needed for crypto) - A BigNumber from Open SSL
options = ['YES', 'NO']

start_time = datetime.now()
print("\n======== EXECUTING PETITION =========\n")

credential_issuer_keypair = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_GENERATE_KEYPAIR)
credential_issuer_verification_keypair = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_PUBLISH_VERIFY, keys=credential_issuer_keypair)


# Generate a citizen keypair and credential (equivalent to "sign_petition_crypto" in the python version
# Which returns a private key and "sigma" which is the credential
def generate_citizen_keypair_and_credential():
    citizen_keypair = execute_contract(CONTRACTS.CITIZEN_KEYGEN)
    citizen_credential_request = execute_contract(CONTRACTS.CITIZEN_CREDENTIAL_REQUEST, keys=citizen_keypair)
    credential_issuer_signed_credential = execute_contract(CONTRACTS.CREDENTIAL_ISSUER_SIGN_CREDENTIAL, keys=credential_issuer_keypair, data=citizen_credential_request)
    citizen_credential = execute_contract(CONTRACTS.CITIZEN_AGGREGATE_CREDENTIAL, keys=citizen_keypair, data=credential_issuer_signed_credential)
    return (citizen_keypair, citizen_credential)


with petition_contract.test_service():
    print("\npetition.init()")
    init_transaction = petition.init()
    token = init_transaction['transaction']['outputs'][0]

    post_transaction(init_transaction, "/init")

    (citizen_A_keypair, citizen_A_credential) = generate_citizen_keypair_and_credential()

    print("\npetition.create_petition()\n")

    create_transaction = petition.create_petition(
        (token,),
        None,
        None,
        petition_UUID,
        citizen_A_credential,
        credential_issuer_verification_keypair
    )

    post_transaction(create_transaction, "/create_petition")

    old_petition = create_transaction['transaction']['outputs'][1]
    old_list = create_transaction['transaction']['outputs'][2]

    # This is not needed until signing
    # credential_proof = execute_contract(CONTRACTS.CITIZEN_PROVE_CREDENTIAL, keys=citizen_A_credential, data=credential_issuer_verification_keypair)
    # print("CREDENTIAL PROOF: ")
    # pp_json(credential_proof)
    #
    # print("VERIFICATION KEYPAIR: ")
    # pp_json(credential_issuer_verification_keypair)



end_time = datetime.now()


print("\n\nSUMMARY:\n")
all_ok = True
for result in results:
    print("RESULT: " + str(result))
    if not (result[0] is True):
        all_ok = False

print("\n\nRESULT OF ALL CONTRACT CALLS: " + str(all_ok) + "\n\n")
print("\n\nTime Taken " + str(datetime.now() - start_time) + "\n\n")
