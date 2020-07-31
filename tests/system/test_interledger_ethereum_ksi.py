from data_transfer.interledger import Interledger, Transfer
from data_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
from .test_setup import setUp, setUp_ksi, create_token, accept_token, transfer_token
from data_transfer.ksi import KSIResponder
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio
import requests
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

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    
    (tokenId,cost) = await create_token(contract_minter_A, token_instance_A, w3_A, tokenId)

    (url_ksi, hash_algorithm, username, password) = setUp_ksi(config)

    print("Test setup ready")

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:
        # mock cleanup to check the transfer reaches the end

        # Create interledger with a bridge in direction from A to B
        print("Building Interledger bridge A -> B")
        inititator = EthereumInitiator(contract_minter_A, contract_address_A, contract_abi_A, url, port=portA)
        responder = KSIResponder(url_ksi, hash_algorithm, username, password)
        interledger = Interledger(inititator, responder)

        print("Creating Intelredger run coroutine")
        

        interledger_task = asyncio.ensure_future(interledger.run())

        print("A smart contract call in ledger A marks the token in 'TransferOut'")

        # Activate token in ledgerA

        await accept_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 2
        await transfer_token(contract_minter_A, token_instance_A, w3_A, tokenId)
        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 1
       
        await asyncio.sleep(2) # Simulate Interledger running

        assert token_instance_A.functions.getStateOfToken(tokenId).call() == 0
        assert len(interledger.transfers) == 1
        assert len(interledger.transfers_sent) == 1
        
        url = responder.url + "/" + interledger.transfers_sent[0].result["tx_hash"]
        # send it as a GET request and check for the result
        ksi_request = requests.get(url, auth=(responder.username, responder.password))
        assert ksi_request.status_code == 200
        assert ksi_request.json()['verificationResult']['status'] == "OK"

        assert len(interledger.results_commit) == 1


        print("Stopping Interledger run coroutine")
        interledger.stop()
        await interledger_task


        print("*----------*")

