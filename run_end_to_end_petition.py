from scripts.zencontract import ZenContract, CONTRACTS

keypair = ZenContract(CONTRACTS.GENERATE_KEYPAIR).execute()

print("Generated Keypair:\n" + keypair)

