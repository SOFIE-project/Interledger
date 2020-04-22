from data_transfer.interledger import Interledger, Transfer
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
    
    create_token(contract_minter_A, token_instance_A, w3_A, tokenId)
    create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
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

        accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        data = transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1
       
        await asyncio.sleep(1) # Simulate Interledger running

        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
        assert len(interledger.transfers) == 1
        assert len(interledger.transfers_sent) == 1
        tx_hash = interledger.transfers_sent[0].result["tx_hash"]
        status = interledger.transfers_sent[0].result["status"]
        tx_info = w3_B.eth.getTransaction(tx_hash)
        tx_receipt = w3_B.eth.getTransactionReceipt(tx_hash)
        
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        #assert tx_info ['from'] == contract_address_A
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
        data = transfer_token(contract_minter_B, token_instance_B, w3_B, tokenId)
        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 1

        await asyncio.sleep(1) # Simulate Interledger running

        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 0
        assert len(interledger.transfers) == 1
        assert len(interledger.transfers_sent) == 1
        tx_hash = interledger.transfers_sent[0].result["tx_hash"]
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        assert tx_info ['blockHash'] != None
        assert tx_info ['hash'] == tx_hash
        #assert tx_info ['from'] == contract_address_B
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


        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task


