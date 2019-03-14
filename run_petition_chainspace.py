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

debug = 0

pp = pprint.PrettyPrinter(indent=4)

# Petition Parameters
petition_UUID = 1234  # petition unique id (needed for crypto) - A BigNumber from Open SSL
options = ['YES', 'NO']

# Set up the petition


print("Petition Setup:")

t_owners = 2  # threshold number of owners
n_owners = 3  # total number of owners

#v = [o.random() for _ in range(0, t_owners)]

#print("threshold seeds for secret keys (v): " + str(v))

#sk_owners = [cu.poly_eval(v, i) % o for i in range(1, n_owners + 1)]

print("\nSecret Keys of the petition owners: ")

# for i in range(n_owners):
#     print("sk[" + str(i) + "] : " + str(sk_owners[i]))

# pk_owner = [xi * g for xi in sk_owners]

print("\nPublic keys of the petition owners: ")
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

print("\nSecret keys of the authorities (Credential issuers):")
# for i in range(n):
#     print("sk_auth[" + str(i) + "] : " + str(sk[i]))

print("\nVerification keys of the authorities (Credential issuers):")
# for i in range(n):
#     print("pk_auth[" + str(i) + "] : " + str(vk[i]))

# aggr_vk = cs.agg_key(bp_params, vk, threshold=True)

#print("\nAggregated Verification Key: " + str(aggr_vk))


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


print("\n======== EXECUTING PETITION =========\n")

start_time = datetime.now()


# def sign_petition_crypto():
#     global d, gamma, private_m, Lambda, ski, sigs_tilde, sigma_tilde, sigs, sigma
#     # some crypto to get the credentials
#     # ------------------------------------
#     # This can be done with zencode "I create my new credential keypair"
#     # Keypair for signer
#     (d, gamma) = cs.elgamal_keygen(bp_params)
#     private_m = [d]  # array containing the private attributes, in this case the private key
#     Lambda = cs.prepare_blind_sign(bp_params, gamma, private_m)  # signer prepares a blind signature request from their private key
#     # This would be done by the authority
#     sigs_tilde = [cs.blind_sign(bp_params, ski, gamma, Lambda) for ski in sk]  # blind sign from each authority
#     # back with the signer, unblind all the signatures, using the private key
#     sigs = [cs.unblind(bp_params, sigma_tilde, d) for sigma_tilde in sigs_tilde]
#     # aggregate all the credentials
#     sigma = cs.agg_cred(bp_params, sigs)
#     return (sigma, d)


with petition_contract.test_service():
    print("\npetition.init()")
    init_transaction = petition.init()
    token = init_transaction['transaction']['outputs'][0]

    post_transaction(init_transaction, "/init")

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
        t_owners,
        n_owners,
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
