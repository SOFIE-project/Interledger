from .test_setup import setUp, create_token, accept_token, transfer_token, commit_transaction, abort_transaction, calculate_used_gas, non_blocking_accept_token, non_blocking_create_token, non_blocking_transfer_token, non_blocking_commit_transaction, non_blocking_abort_transaction
from web3 import Web3
from unittest.mock import patch
import pytest, time, json, os
import asyncio
import time

@pytest.mark.asyncio
async def test_with_two_ethereum_multiple_transfer_without_interledger(config):
    total_cost = 0

    # set up ledgerA and ledgerB
    print("Test setup ready, performing measurement for multiple asset transfers")
    (contract_minter_A, contract_address_A, contract_abi_A, url, portA) = setUp(config, 'left')
    (contract_minter_B, contract_address_B, contract_abi_B, url, portB) = setUp(config, 'right')

    w3_A = Web3(Web3.HTTPProvider(url+":"+str(portA)))
    w3_B = Web3(Web3.HTTPProvider(url+":"+str(portB)))
    token_instance_A = w3_A.eth.contract(abi=contract_abi_A, address=contract_address_A)
    token_instance_B = w3_B.eth.contract(abi=contract_abi_B, address=contract_address_B)
    
    # prepare for asset transfer
    simultaneous_transfers = [1, 2, 5, 10, 20, 50, 100]
    #simultaneous_transfers = [2, 5, 10]
    for transfers in simultaneous_transfers:
        tokens = []
        
        # needed for token creation
        create = []
        
        # these contain tokens transiting between various states
        transfer_out = []
        need_accept = []
        accept = []
        need_commit = []
        commit = []
        completed = []

        # Create tokens in both ledgers and set their state in ledger A
        start_time = time.time()

        filter_A = token_instance_A.events.NewTokenAsset().createFilter(fromBlock = 'latest')
        filter_B = token_instance_B.events.NewTokenAsset().createFilter(fromBlock = 'latest')

        for i in range(transfers):
            (tokenId, tx_hash) = non_blocking_create_token(contract_minter_A, token_instance_A, w3_A)
            (tokenId, tx_hash) = non_blocking_create_token(contract_minter_B, token_instance_B, w3_B, tokenId)
            create.append(tokenId)
            
        while(True):
            # Check wherever token has been created in both ledgers
            to_remove = []
            entries = filter_A.get_new_entries()
            
            for entry in entries:
                token = entry['args']['tokenId']
                if token in create:
                    need_accept.append(token)
                    to_remove.append(token)
                        
            create = [x for x in create if x not in to_remove]

            # Accept created tokens in ledger A
            to_remove = []
            for token in need_accept:
                non_blocking_accept_token(contract_minter_A, token_instance_A, w3_A, token)
                accept.append(token)
                to_remove.append(token)
                
            need_accept = [x for x in need_accept if x not in to_remove]
            
            # Check wherever token is in Here state in ledger A
            to_remove = []
            for token in accept:
                if token_instance_A.functions.getStateOfToken(tokenId).call() == 2:
                    tokens.append(token)
                    to_remove.append(token)
                    
            accept = [x for x in accept if x not in to_remove]
            
            if (len(tokens) == transfers) and (len(need_accept) == 0) and (len(accept) == 0):
                # all tokens have been created and accepted in ledger A
                break

        elapsed_time = time.time() - start_time
        print(f"Token setup ready for {transfers} simultaneous transfers, took: {elapsed_time} seconds")
        #print("\t", tokens)
        

        # Initiate transfer by calling transferOut for each token
        start_time = time.time()
        for token in tokens:
            tx_hash1 = non_blocking_transfer_token(contract_minter_A, token_instance_A, w3_A, token)
            transfer_out.append(token)

        while(True):
            # Check wherever some tokens have moved to TransferOut state
            to_remove = []
            for token in transfer_out:
               if token_instance_A.functions.getStateOfToken(token).call() == 1:
                   need_accept.append(token)
                   to_remove.append(token)
    
            # remove from transfer_out tokens whose state is already TransferOut
            transfer_out = [x for x in transfer_out if x not in to_remove]

            
            # Process tokens for which accept should be called in ledger B
            to_remove = []
            for token in need_accept:
                tx_hash2 = non_blocking_accept_token(contract_minter_B, token_instance_B, w3_B, token)
                accept.append(token)
                to_remove.append(token)
                
            need_accept = [x for x in need_accept if x not in to_remove]
            
            
            # Process accepted tokens, these can be committed to ledger A
            to_remove = []
            for token in accept:
                if token_instance_B.functions.getStateOfToken(token).call() == 2:
                    need_commit.append(token)
                    to_remove.append(token)

            accept = [x for x in accept if x not in to_remove]

            
            # Process tokens for which commit should be called in ledger A 
            to_remove = []
            for token in need_commit:
                tx_hash3 = non_blocking_commit_transaction(contract_minter_A, token_instance_A, w3_A, token)
                commit.append(token)
                to_remove.append(token)
                
            need_commit = [x for x in need_commit if x not in to_remove]
            
            
            # Check wherever transfer has been completed (token is in NotHere state in ledger A)
            to_remove = []
            for token in commit:
                if token_instance_A.functions.getStateOfToken(token).call() == 0:
                    completed.append(token)
                    to_remove.append(token)
                    
            commit = [x for x in commit if x not in to_remove]


            # Check wherever we have completed all transfers
            if len(completed) == transfers:
                elapsed_time = time.time() - start_time
                print(f"Took {elapsed_time} seconds for completing {transfers} transfers\n")
                break
