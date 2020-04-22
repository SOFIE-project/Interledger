from data_transfer.interledger import Transfer, ErrorCode
from data_transfer.ethereum import EthereumInitiator
from .test_setup import setUp, create_token, accept_token, transfer_token
import pytest, asyncio
import os, json
import web3
from web3 import Web3
from uuid import uuid4

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

def test_init(config):

    # Setup web3 and state
    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)

    assert init.web3.isConnected()
    assert init.minter == contract_minter
    #assert init.contract == token_instance
    assert init.timeout == 120

#
# Test get_transfers
#

@pytest.mark.asyncio
async def test_initiator_listen_for_events(config):
    
    # Setup the state
    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    # Create a token
    ids = [uuid4().int, uuid4().int, uuid4().int, uuid4().int]
    tokenURI = "weapons/"
    assetName = w3.toBytes(text="Vorpal Sword")

    for tokenId in ids:

        tx_hash = token_instance.functions.mint(bob, tokenId, tokenURI, assetName).transact({'from': contract_minter})
        w3.eth.waitForTransactionReceipt(tx_hash)
        assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    
        # Change to valid state
        tx_hash = token_instance.functions.accept(tokenId).transact({'from': contract_minter})
        w3.eth.waitForTransactionReceipt(tx_hash)
        assert token_instance.functions.getStateOfToken(tokenId).call() == 2



     ### Test Ethereum Initiator ###

    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)
    
    
    # Emit 1 event and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[0]).transact({'from': bob})
    assert token_instance.functions.getStateOfToken(ids[0]).call() == 1
    w3.eth.waitForTransactionReceipt(tx_hash)
    transfers = await init.listen_for_events()

    t = transfers[0]
    assert len(transfers) == 1
    assert t.payload['id'] == str(ids[0])

    # Emit 2 events and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[1]).transact({'from': bob})
    assert token_instance.functions.getStateOfToken(ids[1]).call() == 1
    tx_hash = token_instance.functions.transferOut(ids[2]).transact({'from': bob})
    assert token_instance.functions.getStateOfToken(ids[2]).call() == 1
    transfers = await init.listen_for_events()

    t = transfers[1]
    assert len(transfers) == 2
    assert t.payload['id'] == str(ids[2])
    


    # Emit 1 event and call get_transfers
    tx_hash = token_instance.functions.transferOut(ids[3]).transact({'from': bob})
    assert token_instance.functions.getStateOfToken(ids[3]).call() == 1
    transfers = await init.listen_for_events()

    assert len(transfers) == 1

#
# Test abort_transfer
#

@pytest.mark.asyncio
async def test_initiator_abort(config):

    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    tokenId = create_token(contract_minter, token_instance, w3)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    accept_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 2
    transfer_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 1
    ### Test Ethereum Initiator ###    

    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)
    reason = 2
    result = await init.abort_sending(str(tokenId), reason)

    assert result["status"] == True


#
# Test commit_transfer
#

@pytest.mark.asyncio
async def test_initiator_commit(config):

    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    tokenId = create_token(contract_minter, token_instance, w3)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    accept_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 2
    transfer_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 1
    ### Test Ethereum Initiator ###

    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)

    result = await init.commit_sending(str(tokenId))

    assert result["status"] == True
