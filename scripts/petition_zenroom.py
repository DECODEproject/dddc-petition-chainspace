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
                    owner_credential,
                    verification_keypair):

    zen_petition = execute_contract(CONTRACTS.CITIZEN_CREATE_PETITION,
                                    keys=owner_credential,
                                    data=verification_keypair)

    petition = {
        "type": "PetitionObject",
        "UUID": petition_uuid,
        "zen_petition": json.loads(zen_petition),
        "verification_keypair": json.loads(verification_keypair)
    }

    return {
        'outputs': (inputs[0], json.dumps(petition)),
    }


# ------------------------------------------------------------------
# sign
# ------------------------------------------------------------------
@contract.method('sign_petition')
def sign_petition(inputs, reference_inputs, parameters, petition_signature):

    old_petition = json.loads(inputs[0])
    zen_petition = old_petition['zen_petition']

    petition_with_signature = execute_contract(CONTRACTS.LEDGER_INCREMENT_PETITION,
                                               keys=json.dumps(zen_petition),
                                               data=petition_signature)

    new_petition = old_petition.copy()
    new_petition['zen_petition'] = json.loads(petition_with_signature)

    return {
        'outputs': (json.dumps(new_petition), ),
        'extra_parameters': (petition_signature, )
    }


# ------------------------------------------------------------------
# tally
# ------------------------------------------------------------------
@contract.method('tally_petition')
def tally_petition(inputs, reference_inputs, parameters, owner_credential):

    petition = json.loads(inputs[0])

    zen_petition = petition['zen_petition']

    tally = execute_contract(CONTRACTS.CITIZEN_TALLY_PETITION,
                             keys=owner_credential,
                             data=json.dumps(zen_petition))

    new_petition = petition.copy()

    new_petition['zen_tally'] = json.loads(tally)

    return {
        'outputs': (json.dumps(new_petition), )
    }


# ------------------------------------------------------------------
# read
# ------------------------------------------------------------------
@contract.method('read_petition')
def read_petition(inputs, reference_inputs, parameters):
    petition = json.loads(reference_inputs[0])

    zen_tally = petition['zen_tally']
    zen_petition = petition['zen_petition']

    tally_count = execute_contract(CONTRACTS.CITIZEN_COUNT_PETITION,
                                   keys=json.dumps(zen_tally),
                                   data=json.dumps(zen_petition))

    return {
        'returns': (tally_count,),
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
        petition = json.loads(outputs[1])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 2 or len(returns) != 0:
            print("CHECKER-FAIL: incorrect inputs and outputs")
            return False

        if petition_token['type'] != 'PetitionToken' or \
                petition['type'] != 'PetitionObject':
            print("CHECKER-FAIL: types incorrect")
            return False

        # check fields
        if petition['UUID'] is None:
            print("CHECKER-FAIL: UUID is empty")
            return False

        if (petition['zen_petition']) is None:
            print("CHECKER-FAIL: no zen_petition")
            return False

        if (petition['verification_keypair']) is None:
            print("CHECKER-FAIL: no verifier")
            return False

        verification_keypair = json.dumps(petition['verification_keypair'])
        zen_petition = json.dumps(petition['zen_petition'])

        verified_petition = execute_contract(CONTRACTS.VERIFIER_APPROVE_PETITION,
                                             keys=verification_keypair,
                                             data=zen_petition)

        # @TODO - could do with a better thing to check here.
        if not (verified_petition.startswith("{") and verified_petition.endswith("}")):
            print("CHECKER-FAIL: could not verify petition!")
            print(verified_petition)
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()

        print("EXCEPTION IN CHECKER:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        return False


# ------------------------------------------------------------------
# check petition's signature
# ------------------------------------------------------------------
@contract.checker('sign_petition')
def sign_petition_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        petition = json.loads(outputs[0])  # outputs are always strings

        # check format
        if len(inputs) is not 1 or \
                len(reference_inputs) is not 0 or \
                len(outputs) is not 1 or \
                len(parameters) is not 1 or \
                len(returns) is not 0:
            print("CHECKER-FAIL: incorrect inputs and outputs:")
            print("inputs: " + str(len(inputs)))
            print("outputs: " + str(len(outputs)))
            print("parameters: " + str(len(parameters)))
            print("returns: " + str(len(returns)))
            return False

        if petition['type'] != 'PetitionObject':
            print("CHECKER-FAIL: types incorrect")
            return False

        # check fields
        if petition['UUID'] is None:
            print("CHECKER-FAIL: UUID is empty")
            return False

        if (petition['zen_petition']) is None:
            print("CHECKER-FAIL: no zen_petition")
            return False

        if (petition['verification_keypair']) is None:
            print("CHECKER-FAIL: no verifier")
            return False

        if (parameters[0]) is None:
            print("CHECKER-FAIL: no signature")
            return False

        # @TODO - need to cryptographically verify that the signature is valid \
        #  and that what went into the petition is good

        signature = parameters[0]
        if not (signature.startswith("{") and signature.endswith("}")):
            print("CHECKER-FAIL: signature is not a valid JSON!")  # this will at least check if zenroom executed ok
            print(signature)
            return False

        return True

    except (KeyError, Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()

        print("EXCEPTION IN CHECKER:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        return False


# ------------------------------------------------------------------
# check petition's signature
# ------------------------------------------------------------------
@contract.checker('tally_petition')
def tally_petition_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        petition = json.loads(outputs[0])  # outputs are always strings

        # check format
        if len(inputs) is not 1 or \
                len(reference_inputs) is not 0 or \
                len(outputs) is not 1 or \
                len(parameters) is not 0 or \
                len(returns) is not 0:
            print("CHECKER-FAIL: incorrect inputs and outputs:")
            print("inputs: " + str(len(inputs)))
            print("outputs: " + str(len(outputs)))
            print("parameters: " + str(len(parameters)))
            print("returns: " + str(len(returns)))
            return False

        if petition['type'] != 'PetitionObject':
            print("CHECKER-FAIL: types incorrect")
            return False

        # check fields
        if petition['UUID'] is None:
            print("CHECKER-FAIL: UUID is empty")
            return False

        if (petition['zen_petition']) is None:
            print("CHECKER-FAIL: no zen_petition")
            return False

        if (petition['verification_keypair']) is None:
            print("CHECKER-FAIL: no verifier")
            return False

        if (petition['zen_tally']) is None:
            print("CHECKER-FAIL: no zen_tally")
            return False


        # @TODO - need to cryptographically verify that the Tally is valid - in the python version it provides a proof

        zen_tally = petition['zen_tally']

        if zen_tally['petition'] is None:
            print("CHECKER-FAIL: no petition in zen_tally")

        if zen_tally['tally'] is None:
            print("CHECKER-FAIL: no tally result in zen_tally")

        return True

    except (KeyError, Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()

        print("EXCEPTION IN CHECKER:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        return False


# ------------------------------------------------------------------
# check petition's signature
# ------------------------------------------------------------------
@contract.checker('read_petition')
def read_petition_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        results = json.loads(returns[0])  # outputs are always strings

        # check format
        if len(inputs) is not 0 or \
                len(reference_inputs) is not 1 or \
                len(outputs) is not 0 or \
                len(parameters) is not 0 or \
                len(returns) is not 1:
            print("CHECKER-FAIL: incorrect inputs and outputs:")
            print("inputs: " + str(len(inputs)))
            print("outputs: " + str(len(outputs)))
            print("parameters: " + str(len(parameters)))
            print("returns: " + str(len(returns)))
            return False

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
