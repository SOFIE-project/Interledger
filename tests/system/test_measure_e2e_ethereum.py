from data_transfer.interledger import Interledger, Transfer, ErrorCode
from data_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
from .test_setup import setUp, create_token, accept_token, transfer_token, commit_transaction, abort_transaction, calculate_used_gas, non_blocking_accept_token, non_blocking_transfer_token, non_blocking_commit_transaction, non_blocking_abort_transaction
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio
import time
from uuid import uuid4

@pytest.mark.asyncio
async def test_interledger_with_two_ethereum(config):
    # set up ledgerA and ledgerB
    total_cost = 0
    tx_hashes = []
    tokenId = uuid4().int

    print("Test setup ready, performing measurement for successful asset transfer")

    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    # asset transfer preparation
    (tokenId,cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    (tokenId,cost) = await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)

    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0


    cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2

    # measuring the performance of an arbitrary asset transfer
    start_time = time.time()
    tx_hash =  non_blocking_transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    tx_hashes.append(tx_hash)

    w3_A.eth.waitForTransactionReceipt(tx_hashes[0])
    tx_hash =  non_blocking_accept_token(contract_minter_B, token_instance_B, w3_B, tokenId)
    tx_hashes.append(tx_hash)

    w3_B.eth.waitForTransactionReceipt(tx_hashes[1])
    tx_hash =  non_blocking_commit_transaction(contract_minter_A, token_instance_A, w3_A, tokenId)
    tx_hashes.append(tx_hash)


    w3_A.eth.waitForTransactionReceipt(tx_hashes[2])
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2
    elapsed_time = time.time() - start_time

    total_cost += calculate_used_gas(tx_hashes[0], w3_A)
    total_cost += calculate_used_gas(tx_hashes[1], w3_B)
    total_cost += calculate_used_gas(tx_hashes[2], w3_A)

    print("Time interval: ", elapsed_time)
    print("Total cost: ", total_cost) 
       
    print("*----------------------------------------------------*")


@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_transaction_failure(config):
    # set up ledgerA and ledgerB
    total_cost = 0
    tx_hashes = []
    tokenId = uuid4().int
    
    print("Test setup ready, performing measurement for unsuccessful asset transfer")

    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    # asset transfer preparation
    start_time = time.time()
    (tokenId, cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    total_cost += cost
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0

    cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    total_cost += cost
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
    elapsed_time = time.time() - start_time
    print("Time interval for token creation: ", elapsed_time)
    print("Total cost for token creation: : ", total_cost)
    total_cost = 0

    # measuring performance of an arbitrary asset transfer
    start_time = time.time()
    tx_hash = await non_blocking_transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    tx_hashes.append(tx_hash)
    
    w3_A.eth.waitForTransactionReceipt(tx_hashes[0])
    tx_hash = await non_blocking_abort_transaction(contract_minter_A, token_instance_A, w3_A, tokenId)
    tx_hashes.append(tx_hash)

    w3_A.eth.waitForTransactionReceipt(tx_hashes[1])
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
    elapsed_time = time.time() - start_time
    for tx_hash in tx_hashes:
        total_cost += calculate_used_gas(tx_hash, w3_A)
    print("Time interval: ", elapsed_time)
    print("Total cost: ", total_cost) 
       
    print("*----------------------------------------------------*")

@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_multiple_transfer(config):
    # set up ledgerA and ledgerB
    total_cost = 0
    ids = [[],[],[],[],[],[]]

    print("Test setup ready, performing measurement for multiple asset transfers")
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    # prepare for asset transfer
    indexes = [2, 5, 10 , 20, 50, 100] 
    for i in range (0,6):
        index = indexes[i]
        #tx_hashes.append([])
        for j in range(0, index):
            #tx_hashes[i].append([])
            tokenId = uuid4().int
            ids[i].append(tokenId)
            (tokenId,cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
            (tokenId,cost) = await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
            assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
            assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
    
            cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
            assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
    
    # issue multiple asset transfers
    # for i in range (0,6):
    #     index = indexes[i]
        start_time = time.time()
        total_cost = 0
        for j in range(0, index):
            tx_hash1 = await non_blocking_transfer_token(contract_minter_A, token_instance_A, w3_A, ids[i][j])

        for j in range(0, index):
            tx_hash2 = await non_blocking_accept_token(contract_minter_B, token_instance_B, w3_B, ids[i][j])

        for j in range(0, index):
            w3_A.eth.waitForTransactionReceipt(tx_hash1)
            tx_hash3 = await non_blocking_commit_transaction(contract_minter_A, token_instance_A, w3_A, ids[i][j])
          
    
        #for j in range(0, index):
            w3_B.eth.waitForTransactionReceipt(tx_hash2)
            w3_A.eth.waitForTransactionReceipt(tx_hash3)
            assert token_instance_A.functions.getStateOfToken(ids[i][j]).call() == 0
            assert token_instance_B.functions.getStateOfToken(ids[i][j]).call() == 2
            total_cost += calculate_used_gas(tx_hash1, w3_A)
            total_cost += calculate_used_gas(tx_hash2, w3_B)
            total_cost += calculate_used_gas(tx_hash3, w3_A)

        elapsed_time = time.time() - start_time
        print("number of transfers: ", index)
        print("Time interval: ", elapsed_time)
        print("Total cost: ", total_cost) 
       
    print("*----------------------------------------------------*")    