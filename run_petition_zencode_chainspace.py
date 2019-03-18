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

    # Citizen A creates the petition
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

    citizen_A_signature = execute_contract(CONTRACTS.CITIZEN_SIGN_PETITION,
                                           keys=citizen_A_credential,
                                           data=credential_issuer_verification_keypair)

    sign_A_tx = petition.sign_petition(
        (old_petition,),
        None,
        None,
        citizen_A_signature
    )

    post_transaction(sign_A_tx, "/sign_petition")

    old_petition = sign_A_tx['transaction']['outputs'][0]


    # Citizen B Signs

    (citizen_B_keypair, citizen_B_credential) = generate_citizen_keypair_and_credential()
    citizen_B_signature = execute_contract(CONTRACTS.CITIZEN_SIGN_PETITION,
                                           keys=citizen_B_credential,
                                           data=credential_issuer_verification_keypair)

    sign_B_tx = petition.sign_petition(
        (old_petition,),
        None,
        None,
        citizen_B_signature
    )

    post_transaction(sign_B_tx, "/sign_petition")

    old_petition = sign_B_tx['transaction']['outputs'][0]


    # Citizen C signs petition
    (citizen_C_keypair, citizen_C_credential) = generate_citizen_keypair_and_credential()

    citizen_C_signature = execute_contract(CONTRACTS.CITIZEN_SIGN_PETITION,
                                           keys=citizen_C_credential,
                                           data=credential_issuer_verification_keypair)

    sign_C_tx = petition.sign_petition(
        (old_petition,),
        None,
        None,
        citizen_C_signature
    )

    post_transaction(sign_C_tx, "/sign_petition")

    old_petition = sign_C_tx['transaction']['outputs'][0]

    tally_tx = petition.tally_petition(
        (old_petition,),
        None,
        None,
        citizen_A_credential
    )

    post_transaction(tally_tx, "/tally_petition")

    old_petition = tally_tx['transaction']['outputs'][0]

    tally_results_tx = petition.read_petition(
        None,
        (old_petition, ),
        None
    )

    post_transaction(tally_results_tx, "/read_petition")

    print(tally_results_tx['transaction']['returns'][0])

end_time = datetime.now()


print("\n\nSUMMARY:\n")
all_ok = True
for result in results:
    print("RESULT: " + str(result))
    if not (result[0] is True):
        all_ok = False

print("\nRESULT OF ALL CONTRACT CALLS: " + str(all_ok))
print("\nTime Taken " + str(datetime.now() - start_time) + "\n\n")
