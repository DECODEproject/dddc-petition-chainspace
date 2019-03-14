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


debug = 0

pp = pprint.PrettyPrinter(indent=4)


def print_json(label, json_str):
    formatted = json.dumps(json.loads(json_str), sort_keys=True, indent=4)
    print(label + ":\n" + formatted)


def execute_contract(contractName, keys=None, data=None):
    contract = ZenContract(contractName)
    contract.keys(keys)
    contract.data(data)
    res = contract.execute()
    if (res is not None) and res.startswith("{"):
        print_json(contractName, res)
    else:
        print(contractName + ":\n" + res)
    return res

def pp_json(json_str):
    pp.pprint(json.loads(json_str))


def pp_object(obj):
    pp.pprint(obj)


results = []


def post_transaction(transaction, path):
    tx = csc.transaction_inline_objects(transaction)
    print("Posting transaction to " + path)
    if debug == 1:
        pp_object(tx)

    start_tx = datetime.now()
    response = requests.post(
        'http://127.0.0.1:5000/'
        + petition_contract.contract_name
        + path,
        json=tx)

    print(response.text)

    client_latency = (datetime.now() - start_tx)
    json_response = json.loads(response.text)
    results.append((json_response['success'], response.url, str(client_latency), transaction['transaction']['methodID']))

    return response


print("Petition Setup:")
petition_UUID = 1234  # petition unique id (needed for crypto) - A BigNumber from Open SSL
options = ['YES', 'NO']

#t_owners = 2  # threshold number of owners
#n_owners = 3  # total number of owners
#v = [o.random() for _ in range(0, t_owners)]
#print("threshold seeds for secret keys (v): " + str(v))
#sk_owners = [cu.poly_eval(v, i) % o for i in range(1, n_owners + 1)]
#print("\nSecret Keys of the petition owners: ")
# for i in range(n_owners):
#     print("sk[" + str(i) + "] : " + str(sk_owners[i]))
# pk_owner = [xi * g for xi in sk_owners]
#print("\nPublic keys of the petition owners: ")
# for i in range(n_owners):
#     print("pk[" + str(i) + "] : " + str_ec_pt(pk_owner[i]))
# l = cu.lagrange_basis(range(1, t_owners + 1), o, 0)
# aggr_pk_owner = cu.ec_sum([l[i] * pk_owner[i] for i in range(t_owners)])
#print("\nAggregate public key for owners: " + str_ec_pt(aggr_pk_owner))
# coconut parameters
# print("Coconut setup")
# t, n = 4, 5  # threshold and total number of authorities
# bp_params = cs.setup()  # bp system's parameters
#
# (sk, vk) = cs.ttp_keygen(bp_params, t, n)  # authorities keys
#print("\nSecret keys of the authorities (Credential issuers):")
# for i in range(n):
#     print("sk_auth[" + str(i) + "] : " + str(sk[i]))
#print("\nVerification keys of the authorities (Credential issuers):")
# for i in range(n):
#     print("pk_auth[" + str(i) + "] : " + str(vk[i]))
# aggr_vk = cs.agg_key(bp_params, vk, threshold=True)
#print("\nAggregated Verification Key: " + str(aggr_vk))
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

    credential_proof = execute_contract(CONTRACTS.CITIZEN_PROVE_CREDENTIAL, keys=citizen_A_credential, data=credential_issuer_verification_keypair)

    # pass the credential proof, and the verifier keys into the petition (need to just get the public part of this?)
    # If we want the citizen to be able to do this on their own we need the verifier keys to get input somehow

    # The cs contract can then verify the proof as part of the checker.

    # then we can actually create a petition as the citizen and the checker can VERIFIER_APPROVE_PETITION in the checker

    create_transaction = petition.create_petition(
        (token,),
        None,
        None,
        petition_UUID,
        options,
        None,
        None,
        #sk_owners[0],  # private key of the owner for signing
        #aggr_pk_owner,  # aggregated public key of the owners
        1,
        1,
        None
        #aggr_vk  # aggregated verifier key
    )
    print("\npetition.create_petition()")

    post_transaction(create_transaction, "/create_petition")

    old_petition = create_transaction['transaction']['outputs'][1]
    old_list = create_transaction['transaction']['outputs'][2]


end_time = datetime.now()


print("\n\nSUMMARY:\n")
all_ok = True
for result in results:
    print("RESULT: " + str(result))
    if not (result[0] is True):
        all_ok = False

print("\n\nRESULT OF ALL CONTRACT CALLS: " + str(all_ok) + "\n\n")
print("\n\nTime Taken " + str(datetime.now() - start_time) + "\n\n")
