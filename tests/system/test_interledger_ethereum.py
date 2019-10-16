from sofie_asset_transfer.interledger import Interledger, Transfer
from sofie_asset_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio

# Helper functions
def readContractData(path):
    with open(path) as obj:
        jsn = json.load(obj)
        return jsn["abi"], jsn["bytecode"]


def create_contract(w3, abi, bytecode, _from):

    # Create contract
    TokenContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = TokenContract.constructor("GameToken", "GAME").transact({'from': _from})
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    address = tx_receipt.contractAddress
    token_instance = w3.eth.contract(abi=abi, address=address)
    return token_instance


# current working directory changes if you run pytest in ./, or ./tests/ or ./tests/system
cwd = os.getcwd()
contract_path = "truffle/build/contracts/GameToken.json"

if "system" in cwd.split('/'):
    contract_path = "../../" + contract_path
elif "tests" in cwd.split('/'):
    contract_path = "../" + contract_path
else:
    contract_path = "./" + contract_path

# # # # Global view
# # #
# # #  LedgerA <- Initiator <- Interledeger -> Responder -> LedgerB
# #


@pytest.mark.asyncio
async def test_interledger_with_two_ethereum():
    
    # Setup web3
    url = "HTTP://127.0.0.1"
    portA = 8545
    portB = 7545
    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    abi, bytecode = readContractData(contract_path)

    contract_minter_A = w3_A.eth.accounts[0]
    contract_minter_B = w3_B.eth.accounts[0]
    bob_A = w3_A.eth.accounts[1]
    bob_B = w3_B.eth.accounts[1]

    token_instance_A = create_contract(w3_A, abi, bytecode, contract_minter_A)
    token_instance_B = create_contract(w3_B, abi, bytecode, contract_minter_B)

    # Initial State
    # Token 123
        # Active in LedgerA: w3_A
        # Inactive in LedgerB: w3_B

    # Create a token
    tokenId = 123
    tokenURI = "weapons/"
    assetId = w3_A.toBytes(text="Vorpal Sword")

        # Ledger A
    token_instance_A.functions.mint(bob_A, tokenId, tokenURI, assetId).transact({'from': contract_minter_A})
        # Ledger A
    token_instance_B.functions.mint(bob_B, tokenId, tokenURI, assetId).transact({'from': contract_minter_B})

        # Activate token in ledgerA
    token_instance_A.functions.accept(tokenId).transact({'from': contract_minter_A})

    print("Test setup ready")

    # Create interledger with a bridge in direction from A to B
    print("Building Interledger bridge A -> B")
    inititator = EthereumInitiator(contract_minter_A, token_instance_A, url, port=portA)
    responder = EthereumResponder(contract_minter_B, token_instance_B, url, port=portB)
    interledger = Interledger(inititator, responder)

    print("Creating Intelredger run coroutine")
    

    interledger_task = asyncio.ensure_future(interledger.run())

    print("A smart contract call in ledger A marks the token in 'TransferOut'")
    token_instance_A.functions.transferOut(tokenId).transact({'from': bob_A})

    await asyncio.sleep(1) # Simulate Interledger running

    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
    assert len(interledger.transfers_sent) == 1
    assert len(interledger.results_commit) == 1

    print("Stopping Interledger run coroutine")
    interledger.stop()
    await interledger_task


    print("*----------*")


    print("Building Interledger bridge B -> A")
    inititator = EthereumInitiator(contract_minter_B, token_instance_B, url, port=portB)
    responder = EthereumResponder(contract_minter_A, token_instance_A, url, port=portA)
    interledger = Interledger(inititator, responder)

    print("Creating Intelredger run coroutine")

    interledger_task = asyncio.ensure_future(interledger.run())

    print("A smart contract call in ledger B marks the token in 'TransferOut'")

    token_instance_B.functions.transferOut(tokenId).transact({'from': bob_B})

    await asyncio.sleep(1) # Simulate Interledger running

    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
    assert len(interledger.transfers_sent) == 1
    assert len(interledger.results_commit) == 1


    print("Stopping Interledger run coroutine")
    interledger.stop()
    await interledger_task



