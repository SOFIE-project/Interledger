from data_transfer.interledger import Interledger, Transfer, ErrorCode
from data_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
from .test_setup import setUp, create_token, accept_token, transfer_token, calculate_used_gas, non_blocking_accept_token, non_blocking_transfer_token, non_blocking_commit_transaction, non_blocking_abort_transaction, non_blocking_create_token
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio
import time
from uuid import uuid4

# # # Global view
#
#  LedgerA <- Initiator <- Interledeger -> Responder -> LedgerB



@pytest.mark.asyncio
async def test_interledger_with_two_ethereum(config):
    # set up ledgerA and ledgerB
    total_cost = 0
    tx_hashes = []
    tokenId = uuid4().int
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    (tokenId,cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    (tokenId,cost) = await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
    
    # Activate token in ledgerA

    cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2

    print("Test setup ready, performing measurement for successful asset transfer")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end
        
        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B")
        start_time = time.time()
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine")
        
        
        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'")

        (data, blockNumber,gas_used)= await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
       
        await asyncio.sleep(1.5) # Simulate Interledger running, should be longer than block time

        tx_hash = interledger.transfers_sent[0].result["tx_hash"]
        tx_hashes.append(tx_hash)

        tx_hash = interledger.results_commit[0]["commit_tx_hash"]
        tx_hashes.append(tx_hash)


        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2 # Here
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0 # Not Here

        elapsed_time = time.time() - start_time
        print("Time interval: ", elapsed_time)

        
        total_cost += gas_used
        total_cost += calculate_used_gas(tx_hashes[0], w3_B)
        total_cost += calculate_used_gas(tx_hashes[1], w3_A)
        print("Total cost: ", total_cost) 

        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task
        print("*----------------------------------------------------*")


@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_transaction_failure(config):
    # set up ledgerA and ledgerB
    tokenId = uuid4().int
    total_cost = 0
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)

    (tokenId, cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    # Activate token in ledgerA
    cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
    #the token will not be created on ledgerB to emulate transaction failure on the responder side 

    print("Test setup ready, performing measurement for unsuccessful asset transfer")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end

        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B...")
        start_time = time.time()
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine...")


        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'...")

        (data, blockNumber,gas_used)= await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)

        await asyncio.sleep(1.5) # Simulate Interledger running, should be longer than block time

        tx_hash = interledger.results_abort[0]["abort_tx_hash"]
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        
        elapsed_time = time.time() - start_time
        print("Time interval: ", elapsed_time)
        
        total_cost += gas_used
        total_cost += calculate_used_gas(tx_hash, w3_A)

        print("Total cost: ", total_cost)
        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task
        print("*----------------------------------------------------*")


@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_multiple_transfer(config):
   
#set up ledgerA and ledgerB
    ids = [[],[],[],[],[],[]]
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    #prepare for asset transfer
    indexes = [2, 5, 10, 20, 50, 100] #
    for i in range (0,6):
        index = indexes[i]
        for j in range(0, index):
            tokenId = uuid4().int
            ids[i].append(tokenId)
            (tokenId,cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
            (tokenId,cost) = await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
            assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
            assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
            #Activate token in ledgerA
            cost = await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
            assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2

        print("Test setup ready, performing measurement for multiple asset transfers")

        with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        #mock cleanup to check the transfer reaches the end

        #Create interledger with a bridge in direction from A to B
            print("Building Interledger bridge A -> B")
            inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
            responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
            interledger = Interledger(inititator, responder)

            print("Creating Intelredger run coroutine")
        
    
            interledger_task = asyncio.ensure_future(interledger.run())

            print("A smart contract call in ledger A marks the token in 'TransferOut'")

            start_time = time.time()
            total_cost = 0
            for j in range(0, index):
                (data, blockNumber,gas_used)= await transfer_token(contract_minter_A, token_instance_A, w3_A, ids[i][j])
                total_cost += gas_used 
        
            await asyncio.sleep(1.5*index) # Simulate Interledger running, should be longer than block time

            for j in range(0, index):
                tx_hash1 = interledger.transfers_sent[j].result["tx_hash"]
                tx_hash2 = interledger.results_commit[j]["commit_tx_hash"]

                assert token_instance_B.functions.getStateOfToken(ids[i][j]).call() == 2 # Here
                assert token_instance_A.functions.getStateOfToken(ids[i][j]).call() == 0 # Not Here

                total_cost += calculate_used_gas(tx_hash1, w3_B)
                total_cost += calculate_used_gas(tx_hash2, w3_A)
            elapsed_time = time.time() - start_time
            print("number of transfers: ", index)
            print("time: ", elapsed_time)
            print("Total cost: ", total_cost) 
            
            print("Stopping Interledger run coroutine")
            interledger.stop()
            await interledger_task


        print("*----------------------------------------------------*")

