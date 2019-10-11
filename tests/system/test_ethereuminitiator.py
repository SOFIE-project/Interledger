from sofie_asset_transfer.interledger import Transfer
from sofie_asset_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
import pytest, time
import asyncio 
import json, time
from web3 import Web3
import os

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


# # # Global view
# #
# #  Ledger <- Initiator <- Interledeger -> Responder -> Ledger
#

###################################

# # # Local view
# #
# #  Ledger <- EthereumInitiator
#
# # 
#

#
# Test get_transfers
#

@pytest.mark.asyncio
async def test_initiator_get_transfers():

    # Setup the state
        # Deploy contract
        # Mint token
        # Call accept() from the minter

    # Setup web3 and state
    url = "HTTP://127.0.0.1"
    port = 8545
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))

    abi, bytecode = readContractData(contract_path)

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    token_instance = create_contract(w3, abi, bytecode, contract_minter)

    # Create a token
    ids = [123, 124, 125, 126]
    tokenURI = "weapons/"
    assetId = w3.toBytes(text="Vorpal Sword")

    for tokenId in ids:

        token_instance.functions.mint(bob, tokenId, tokenURI, assetId).transact({'from': contract_minter})
        # Change to valid state
        token_instance.functions.accept(tokenId).transact({'from': contract_minter})


    ### Test Ethereum Initiator ###

    init = EthereumInitiator(contract_minter, token_instance, url, port=port)

    # Emit 1 event and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[0]).transact({'from': bob})
    transfers = await init.get_transfers()

    t = transfers[0]
    assert len(transfers) == 1
    assert t.data['assetId'] == ids[0]
    assert t.data['from'] == bob

    # Emit 2 events and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[1]).transact({'from': bob})
    tx_hash = token_instance.functions.transferOut(ids[2]).transact({'from': bob})
    transfers = await init.get_transfers()

    assert len(transfers) == 2

    # Emit 1 event and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[3]).transact({'from': bob})
    transfers = await init.get_transfers()

    assert len(transfers) == 1

    
#
# Test abort_transfer
#

@pytest.mark.asyncio
async def test_initiator_abort():

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
    # Change to valid state
    token_instance.functions.accept(tokenId).transact({'from': contract_minter})
    token_instance.functions.transferOut(tokenId).transact({'from': bob})

    t = Transfer()
    t.data = dict()
    t.data["assetId"] = tokenId


    ### Test Ethereum Initiator ###
    

    init = EthereumInitiator(contract_minter, token_instance, url, port=port)

    result = await init.abort_transfer(t)

    assert result == True


#
# Test commit_transfer
#

@pytest.mark.asyncio
async def test_initiator_commit():

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
    # Change to valid state
    token_instance.functions.accept(tokenId).transact({'from': contract_minter})
    token_instance.functions.transferOut(tokenId).transact({'from': bob})

    t = Transfer()
    t.data = dict()
    t.data["assetId"] = tokenId


    ### Test Ethereum Initiator ###
    

    init = EthereumInitiator(contract_minter, token_instance, url, port=port)

    result = await init.commit_transfer(t)

    assert result == True