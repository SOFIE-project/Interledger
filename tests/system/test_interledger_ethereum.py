from data_transfer.interledger import Interledger, Transfer, ErrorCode
from data_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
from .test_setup import setUp, create_token, accept_token, transfer_token
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio
from uuid import uuid4

# # # # Global view
# # #
# # #  LedgerA <- Initiator <- Interledeger -> Responder -> LedgerB
# #


@pytest.mark.asyncio
async def test_interledger_with_two_ethereum(config):
    # set up ledgerA and ledgerB
    tokenId = uuid4().int
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0

    print("Test setup ready")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end

        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B")
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine")
        

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'")

        # Activate token in ledgerA

        await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        (data, blockNumber, gas_used) = await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1
       
        await asyncio.sleep(4) # Simulate Interledger running, should be longer than block time

        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2 # Here
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0 # Not Here

        assert len(interledger.transfers) == 1
        assert len(interledger.results_commit) == 1
        print(interledger.results_commit[0])
        tx_hash = interledger.results_commit[0]["tx_hash"]
        status = interledger.results_commit[0]["status"]
        assert status == True
        tx_info = w3_B.eth.getTransaction(tx_hash)
        tx_receipt = w3_B.eth.getTransactionReceipt(tx_hash)
        
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_B
        print(tx_info)
        
        # check function name and abi
        decoded_input = token_instance_B.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_B.get_function_by_name("interledgerReceive").fn_name
        assert decoded_input[0].abi == token_instance_B.get_function_by_name("interledgerReceive").abi
        
        # check function parameters
        assert decoded_input[1]['data'] == data
        nonce = decoded_input[1]['nonce']
        
        # check for accepted/rejected events
        logs_accept = token_instance_B.events.InterledgerEventAccepted().processReceipt(tx_receipt)
        logs_reject = token_instance_B.events.InterledgerEventRejected().processReceipt(tx_receipt)

        assert len(logs_accept) == 1
        assert logs_accept[0]['args']['nonce'] == nonce
        assert len(logs_reject) == 0
        
        assert len(interledger.results_commit) == 1
        tx_hash = interledger.results_commit[0]["commit_tx_hash"]
        status = interledger.results_commit[0]["commit_status"]
        assert status == True
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_A
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_A.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_A.get_function_by_signature('interledgerCommit(uint256)').fn_name
        assert decoded_input[0].abi == token_instance_A.get_function_by_signature('interledgerCommit(uint256)').abi
        # check function parameters
        assert decoded_input[1]['tokenId'] == tokenId


        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task


        print("*----------*")


        print("Building Interledger bridge B -> A")
        inititator = EthereumInitiator(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        responder = EthereumResponder(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine")

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger B marks the token in 'TransferOut'")
        (data, blockNumber, gas_used) = await transfer_token(contract_minter_B, token_instance_B, w3_B, tokenId)
        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 1

        await asyncio.sleep(4) # Simulate Interledger running, should be longer than block time

        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
        assert len(interledger.transfers) == 1
        assert len(interledger.results_commit) == 1
        tx_hash = interledger.results_commit[0]["tx_hash"]
        status = interledger.results_commit[0]["status"]
        assert status == True
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        assert tx_info ['blockHash'] != None
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['to'] == contract_address_A
        print(tx_info)
        
        # check function name and abi
        decoded_input = token_instance_A.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_A.get_function_by_name("interledgerReceive").fn_name
        assert decoded_input[0].abi == token_instance_A.get_function_by_name("interledgerReceive").abi
        
        # check function parameters
        assert decoded_input[1]['data'] == data
        nonce = decoded_input[1]['nonce']


        # check for accepted/rejected events
        logs_accept = token_instance_A.events.InterledgerEventAccepted().processReceipt(tx_receipt)
        logs_reject = token_instance_A.events.InterledgerEventRejected().processReceipt(tx_receipt)
        assert len(logs_accept) == 1
        assert logs_accept[0]['args']['nonce'] == nonce
        assert len(logs_reject) == 0

        assert len(interledger.results_commit) == 1

        tx_hash = interledger.results_commit[0]["commit_tx_hash"]
        status = interledger.results_commit[0]["commit_status"]
        assert status == True
        tx_info = w3_B.eth.getTransaction(tx_hash)
        tx_receipt = w3_B.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_B
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_B.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_B.get_function_by_signature('interledgerCommit(uint256)').fn_name
        assert decoded_input[0].abi == token_instance_B.get_function_by_signature('interledgerCommit(uint256)').abi
        # check function parameters
        assert decoded_input[1]['tokenId'] == tokenId


        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task



@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_reject_event(config):
    # set up ledgerA and ledgerB
    tokenId = uuid4().int
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    await create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
    assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0

    print("Test setup ready")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end

        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B...")
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine...")

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'...")

        # Activate token in ledgerA
        await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        (data, blockNumber, gas_used) = await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1

        # Activate token in ledgerB to trigger reject event
        await accept_token(contract_minter_B, token_instance_B, w3_B, tokenId)
        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2
        await asyncio.sleep(4) # Simulate Interledger running, should be longer than block time
        
        assert len(interledger.transfers) == 1
        assert len(interledger.results_abort) == 1

        tx_hash = interledger.results_abort[0]["tx_hash"]
        status = interledger.results_abort[0]["status"]
        assert status == False
        tx_info = w3_B.eth.getTransaction(tx_hash)
        tx_receipt = w3_B.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_B
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_B.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_B.get_function_by_name("interledgerReceive").fn_name
        assert decoded_input[0].abi == token_instance_B.get_function_by_name("interledgerReceive").abi
        # check function parameters
        assert decoded_input[1]['data'] == data
        nonce = decoded_input[1]['nonce']
        # check for accepted/rejected events
        logs_accept = token_instance_B.events.InterledgerEventAccepted().processReceipt(tx_receipt)
        logs_reject = token_instance_B.events.InterledgerEventRejected().processReceipt(tx_receipt)
        print (logs_reject)
        assert len(logs_accept) == 0
        assert len(logs_reject) == 1 
        assert logs_reject[0]['args']['nonce'] == nonce

        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2

        assert len(interledger.results_commit) == 0
        assert len(interledger.results_abort) == 1

        tx_hash = interledger.results_abort[0]["abort_tx_hash"]
        status = interledger.results_abort[0]["abort_status"]
        assert status == True
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_A
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_A.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_A.get_function_by_name("interledgerAbort").fn_name
        assert decoded_input[0].abi == token_instance_A.get_function_by_name("interledgerAbort").abi
        # check function parameters
        assert decoded_input[1]['tokenId'] == tokenId
        assert decoded_input[1]['reason'] == 2 #ErrorCode.TRANSACTION_FAILURE
        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task



@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_transaction_failure(config):
    # set up ledgerA and ledgerB
    tokenId = uuid4().int
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    #the token will not be created on ledgerB to emulate transaction failure on the responder side 

    assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0

    print("Test setup ready")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end

        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B...")
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = EthereumResponder(contract_minter_B, contract_address_B, contract_abi_B, url, port=portB)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine...")

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'...")

        # Activate token in ledgerA
        await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        (data, blockNumber, gas_used) = await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1

        await asyncio.sleep(4) # Simulate Interledger running, should be longer than block time

        assert len(interledger.transfers) == 1
        assert len(interledger.results_abort) == 1

        tx_hash = interledger.results_abort[0]["tx_hash"]
        status = interledger.results_abort[0]["status"]
        assert tx_hash == None
        assert status == False
        
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2

        assert len(interledger.results_commit) == 0
        assert len(interledger.results_abort) == 1

        tx_hash = interledger.results_abort[0]["abort_tx_hash"]
        status = interledger.results_abort[0]["abort_status"]
        assert status == True
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        assert tx_info ['to'] == contract_address_A
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_A.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_A.get_function_by_name("interledgerAbort").fn_name
        assert decoded_input[0].abi == token_instance_A.get_function_by_name("interledgerAbort").abi
        # check function parameters
        assert decoded_input[1]['tokenId'] == tokenId
        assert decoded_input[1]['reason'] == 2 #ErrorCode.TRANSACTION_FAILURE
        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task
