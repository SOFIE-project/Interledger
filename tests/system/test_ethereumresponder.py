from sofie_asset_transfer.interledger import Transfer
from sofie_asset_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
import pytest, time
import asyncio 
import json, time, os
from web3 import Web3

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

# # # Local view
# #
# #  EthereumResponder -> Ledger
#
# # 
#

#
# Test receive_transfer
#

@pytest.mark.asyncio
async def test_responder_receive():

    # Setup the state
        # Deploy contract
        # Mint token
        # Call accept() from the minter
        # Call transferOut() from token owner
        
    # Setup web3 and state
    url = "HTTP://127.0.0.1"
    port = 8545
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))

    abi, bytecode = readContractData(contract_path)

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    token_instance = create_contract(w3, abi, bytecode, contract_minter)

    # Create a token
    tokenId = 123
    tokenURI = "weapons/"
    assetId = w3.toBytes(text="Vorpal Sword")

    token_instance.functions.mint(bob, tokenId, tokenURI, assetId).transact({'from': contract_minter})

    t = Transfer()
    t.data = dict()
    t.data["assetId"] = tokenId


    ### Test Ethereum Responder ###
    

    init = EthereumResponder(contract_minter, token_instance, url, port=port)

    result = await init.receive_transfer(t)

    assert result == True