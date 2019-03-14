"""
	A simple smart contract illustarting an e-petition.
"""

# chainspace
from chainspacecontract import ChainspaceContract
####################################################################
# imports
####################################################################
# general
from json import dumps, loads

## contract name
contract = ChainspaceContract('petition')


####################################################################
# methods
####################################################################
# ------------------------------------------------------------------
# init
# ------------------------------------------------------------------
@contract.method('init')
def init():
    return {
        'outputs': (dumps({'type': 'PetitionToken'}),),
    }


# ------------------------------------------------------------------
# create petition
# ------------------------------------------------------------------
@contract.method('create_petition')
def create_petition(inputs, reference_inputs, parameters,
                    petittionUUID, options,
                    petition, credential_issuer_verification_keypair):
    scores = [0, 0]
    # new petition object
    new_petition = {
        'type': 'PetitionObject',
        'UUID': petittionUUID,  # unique ID of the petition
        'options': options,  # the options
        'scores': scores,  # the signatures per option
    }


    spent_list = {
        'type': 'SpentList',
        'list': []
    }

    return {
        'outputs': (inputs[0], dumps(new_petition), dumps(spent_list)),
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
        petition = loads(outputs[1])
        spent_list = loads(outputs[2])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 3 or len(returns) != 0:
            return False

        # check types
        if loads(inputs[0])['type'] != 'PToken' or loads(outputs[0])['type'] != 'PToken': return False
        if petition['type'] != 'PObject' or spent_list['type'] != 'PList': return False

        # check fields
        petition['UUID']  # check presence of field
       # petition['verifier']  # check presence of field
        petition['t_owners']  # check presence of field
        petition['n_owners']  # check presence of field
        options = petition['options']
        scores = petition['scores']
        # pub_owner = unpack(petition['owner'])
        # if len(options) < 1 or len(options) != len(scores): return False
        #
        # # check initalised scores
        # pet_params = pet_setup()
        # (G, g, hs, o) = pet_params
        # zero = (G.infinite(), G.infinite())
        # if not all(init_score == pack(zero) for init_score in scores): return False

        # verify signature
        # hasher = sha256()
        # hasher.update(outputs[1].encode('utf8'))
        # sig = unpack(parameters[0])
        # if not do_ecdsa_verify(pet_params[0], pub_owner, sig, hasher.digest()): return False

        # verify that the spent list & results store are empty
        if spent_list['list'] or petition['dec']: return False

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
