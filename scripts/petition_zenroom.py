"""
    A simple smart contract illustarting an e-petition.
"""

####################################################################
# imports
####################################################################
# general
import json
import pprint
import sys, traceback

# chainspace
from chainspacecontract import ChainspaceContract

from scripts.zencontract import ZenContract, CONTRACTS

pp = pprint.PrettyPrinter(indent=4)


def print_json(contract_name, result):
    print(contract_name + ":foo")
    pp_json(result)


# contract name
contract = ChainspaceContract('petition')

debug = 0


def execute_contract(contract_name, keys=None, data=None):
    zen_contract = ZenContract(contract_name)
    zen_contract.keys(keys)
    zen_contract.data(data)
    res = zen_contract.execute()

    if debug is 1:
        if (res is not None) and res.startswith("{"):
            print_json(contract_name, res)
        else:
            print(contract_name + ":\n" + res)
    return res


def pp_json(json_str):
    pp.pprint(json.loads(json_str))


def pp_object(obj):
    pp.pprint(obj)


####################################################################
# methods
####################################################################
# ------------------------------------------------------------------
# init
# ------------------------------------------------------------------
@contract.method('init')
def init():
    return {
        'outputs': (json.dumps({'type': 'PetitionToken'}),),
    }


# ------------------------------------------------------------------
# create petition
# ------------------------------------------------------------------
# This goes in the verifier
# verified_petition = execute_contract(CONTRACTS.VERIFIER_APPROVE_PETITION, keys=credential_issuer_verification_keypair, data=citizen_petition)

# Everything needed is in the petition. The checker just needs to run VERIFIER_APPROVE_PETITION
# You need the reference inputs and parameters because its part of the framework
@contract.method('create_petition')
def create_petition(inputs, reference_inputs, parameters,
                    petition_uuid,
                    owner_credentials,
                    verification_keypair):

    contract_result = execute_contract(CONTRACTS.CITIZEN_CREATE_PETITION,
                                       keys=owner_credentials,
                                       data=verification_keypair)

    petition_content = json.loads(contract_result)

    new_petition = {
        "type": "PetitionObject",
        "UUID": petition_uuid,
        "verification_keypair": json.loads(verification_keypair)
    }

    new_petition.update(petition_content)

    pp_object(new_petition)

    spent_list = {
        'type': 'SpentList',
        'list': []
    }

    return {
        'outputs': (inputs[0], json.dumps(new_petition), json.dumps(spent_list)),
    }


####################################################################
# checker
####################################################################
# ------------------------------------------------------------------
# check petition's creation
# ------------------------------------------------------------------
@contract.checker('create_petition')
def create_petition_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        # retrieve inputs
        petition_token = json.loads(outputs[0])
        petition_tx = json.loads(outputs[1])
        spent_list = json.loads(outputs[2])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 3 or len(returns) != 0:
            print("CHECKER-FAIL: incorrect inputs and outputs")
            return False

        if petition_token['type'] != 'PetitionToken' or \
                petition_tx['type'] != 'PetitionObject' or \
                spent_list['type'] != 'SpentList':

            print("CHECKER-FAIL: types incorrect")
            return False

        # check fields
        if petition_tx['UUID'] is None:
            print("CHECKER-FAIL: UUID is empty")
            return False

        if (petition_tx['verifier']) is None:
            print("CHECKER-FAIL: no verifier")
            return False

        verification_keypair = json.dumps(petition_tx['verification_keypair'])
        petition = json.dumps(petition_tx)

        verified_petition = execute_contract(CONTRACTS.VERIFIER_APPROVE_PETITION,
                                             keys=verification_keypair,
                                             data=petition)

        # @TODO - could do with a better thing to check here.
        if not (verified_petition.startswith("{") and verified_petition.endswith("}")):
            print("CHECKER-FAIL: could not verify petition!")
            print(verified_petition)
            return False

        # verify that the spent list & results store are empty
        if spent_list['list']:
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()

        print("EXCEPTION IN CHECKER:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        return False


####################################################################
# main
####################################################################
if __name__ == '__main__':
    contract.run()

####################################################################
