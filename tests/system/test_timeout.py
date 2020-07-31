from data_transfer.interledger import Interledger, Transfer, ErrorCode
from data_transfer.ethereum import EthereumInitiator, EthereumResponder
from .test_setup import setUp, create_token, accept_token, transfer_token
from unittest.mock import patch
import pytest, asyncio
import os, json
import web3
from web3 import Web3
from uuid import uuid4
from eth_abi import encode_abi

# Set this variable to True to execute these tests
# Remember to have an ethereum instance with mining time *NOT* automatic (like in ganache)
ENABLE_THIS_TESTS = True

@pytest.mark.asyncio
async def test_responder_receive_timeout(config):

    if not ENABLE_THIS_TESTS:
        return 

    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    (tokenId,cost) = await create_token(contract_minter, token_instance, w3)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    ### Test Ethereum Responder ###
    
    resp = EthereumResponder(contract_minter, contract_address, contract_abi, url, port=port)

    data = encode_abi(['uint256'], [tokenId])
    nonce = "42"
    resp.timeout = 0
    result = await resp.send_data(nonce, data)
    assert result["status"] == False
    assert result["error_code"] == ErrorCode.TIMEOUT

@pytest.mark.asyncio
async def test_initiator_abort_txerror(config):

    if not ENABLE_THIS_TESTS:
      return 

    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    (tokenId,cost) = await create_token(contract_minter, token_instance, w3)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    await accept_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 2
    await transfer_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 1

    reason = 3
    

    ### Test Ethereum Initiator ###

    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)
    init.timeout = 0
    result = await init.abort_sending(str(tokenId), reason)

    assert result["abort_status"] == False
    assert result["abort_error_code"] == ErrorCode.TIMEOUT


@pytest.mark.asyncio
async def test_initiator_commit_txerror(config):

    if not ENABLE_THIS_TESTS:
      return 
    (contract_minter, contract_address, contract_abi, url, port) = setUp(config, 'left')
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    token_instance = w3.eth.contract(abi=contract_abi, address=contract_address)
    (tokenId,cost) = await create_token(contract_minter, token_instance, w3)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 0
    await accept_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 2
    await transfer_token(contract_minter, token_instance, w3, tokenId)
    assert token_instance.functions.getStateOfToken(tokenId).call() == 1

    id = '2'

    ### Test Ethereum Initiator ###

    init = EthereumInitiator(contract_minter, contract_address, contract_abi, url, port=port)
    init.timeout = 0
    result = await init.commit_sending(str(tokenId))

    assert result["commit_status"] == False
    assert result["commit_error_code"] == ErrorCode.TIMEOUT







@pytest.mark.asyncio
async def test_interledger_with_two_ethereum_abort__txerror(config):
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
        responder.timeout = 0
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine")
        

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'")

        # Activate token in ledgerA
        #change_state_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1
       
        await asyncio.sleep(1) # Simulate Interledger running

        print ("token ledger A", token_instance_B.functions.getStateOfToken(tokenId).call())

        assert token_instance_B.functions.getStateOfToken(tokenId).call() == 2 # just collecting tx_receipt is failing not transaction itself
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        assert len(interledger.transfers) == 1
        assert len(interledger.transfers_sent) == 1
        assert interledger.transfers_sent[0].result["status"] == False
        assert interledger.transfers_sent[0].result["error_code"] == ErrorCode.TIMEOUT


        tx_hash = interledger.transfers_sent[0].result["tx_hash"]
        tx_info = w3_B.eth.getTransaction(tx_hash)
        assert tx_info ['blockHash'] != None

        assert len(interledger.results_commit) == 0
        assert len(interledger.results_abort) == 1

        tx_hash = interledger.results_abort[0]["abort_tx_hash"]
        status = interledger.results_abort[0]["abort_status"]
        tx_info = w3_A.eth.getTransaction(tx_hash)
        tx_receipt = w3_A.eth.getTransactionReceipt(tx_hash)
        # check also other information about the transaction
        assert tx_info ['hash'] == tx_hash
        assert tx_info ['blockHash'] != None
        #assert tx_info ['from'] == contract_address_A
        assert tx_info ['to'] == contract_address_A
        print(tx_info)
        # check function name and abi
        decoded_input = token_instance_A.decode_function_input(tx_info['input'])
        assert decoded_input[0].fn_name == token_instance_A.get_function_by_name("interledgerAbort").fn_name
        assert decoded_input[0].abi == token_instance_A.get_function_by_name("interledgerAbort").abi
        # check function parameters
        assert decoded_input[1]['tokenId'] == tokenId
        assert decoded_input[1]['reason'] == 2
        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task


        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task

