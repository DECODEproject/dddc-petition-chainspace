"""
    A simple smart contract illustarting an e-petition.
"""

####################################################################
# imports
####################################################################
# general
import json
import pprint

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
                    owner_credential_proof,
                    verification_keypair):

    contract_result = execute_contract(CONTRACTS.CITIZEN_CREATE_PETITION,
                                       keys=owner_credential_proof,
                                       data=verification_keypair)

    print(contract_result)
    petition_content = json.loads(contract_result)

    new_petition = {
        "type": "PetitionObject",
        "UUID": petition_uuid,  # unique ID of the petition
    }

    new_petition.update(petition_content)

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
        petition_tx = json.loads(outputs[1])
        spent_list = json.loads(outputs[2])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 3 or len(returns) != 0:
            return False

        # check types
        if json.loads(inputs[0])['type'] != 'PetitionToken' or \
                json.loads(outputs[0])['type'] != 'PetitionToken':
            return False

        if petition_tx['type'] != 'PetitionObject' or \
                spent_list['type'] != 'SpentList':
            return False

        # check fields
        if petition_tx['UUID'] is None:
            return False

        if (petition_tx['petition']) is None:
            return False

        petition = petition_tx['petition']

        # verified_petition = execute_contract(CONTRACTS.VERIFIER_APPROVE_PETITION,
        #                                      keys=credential_issuer_verification_keypair,
        #                                      data=petition)

        # verify that the spent list & results store are empty
        if spent_list['list']:
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        return False


####################################################################
# main
####################################################################
if __name__ == '__main__':
    contract.run()

####################################################################
