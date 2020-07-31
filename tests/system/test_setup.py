from configparser import ConfigParser
from start_interledger import parse_ethereum, parse_ksi
import pytest, asyncio
import os, json
import web3
from web3 import Web3
from uuid import uuid4


# Helper function to read KSI related options from configuration file
def setUp_ksi(config_file):
    
    parser = ConfigParser()
    parser.read(config_file)
    right = parser.get('service', 'right')
    
    url, hash_algorithm, username, password = parse_ksi(parser, right)
    return (url, hash_algorithm, username, password)


def setUp(config_file, ledger_name):
    parser = ConfigParser()
    parser.read(config_file)
    ledger = parser.get('service', ledger_name)
    ledger_type = parser.get(ledger, 'type')

    if ledger_type == "ethereum":
        (contract_minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, ledger)

    else:
        print(f"WARNING: ledger type {ledger_type} not supported yet")
        exit(1)

    return (contract_minter, contract_address, contract_abi, url, port)


async def create_token(contract_minter, token_instance, w3, tokenId = None):
    # Create a token
    if(tokenId == None):
        tokenId = uuid4().int
    tokenURI = "weapons/"
    assetName = w3.toBytes(text="Vorpal Sword")

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.mint(w3.eth.accounts[1], tokenId, tokenURI, assetName).transact({'from': contract_minter})
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_info = w3.eth.getTransaction(tx_hash)
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    gas_used = tx_receipt['gasUsed'] 
    gas_price = int(tx_info ['gasPrice']) * (10**(-9)) #convert to gwei
    cost = gas_price * gas_used * (10**(-9)) #convert to ether
    return (tokenId, gas_used)

async def accept_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to here 
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.accept(tokenId).transact({'from': contract_minter})
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_info = w3.eth.getTransaction(tx_hash)
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    gas_used = tx_receipt['gasUsed'] 
    gas_price = int(tx_info ['gasPrice']) * (10**(-9)) #convert to gwei
    cost = gas_price * gas_used * (10**(-9)) #convert to ether
    return gas_used

async def commit_transaction(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[0]

    tx_hash = token_instance.functions.interledgerCommit(tokenId).transact({'from': bob}) 
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    
    tx_info = w3.eth.getTransaction(tx_hash)
    gas_used = receipt['gasUsed'] 
    gas_price = int(tx_info ['gasPrice']) * (10**(-9)) #convert to gwei
    cost = gas_price * gas_used * (10**(-9)) #convert to ether
    return gas_used

async def abort_transaction(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[0]
    reason = 4
    tx_hash = token_instance.functions.interledgerAbort(tokenId, reason).transact({'from': bob}) 
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    

    tx_info = w3.eth.getTransaction(tx_hash)
    gas_used = receipt['gasUsed'] 
    gas_price = int(tx_info ['gasPrice']) * (10**(-9)) # convert to gwei
    cost = gas_price * gas_used * (10**(-9)) # convert to ether
    return gas_used  #cost
async def transfer_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.transferOut(tokenId).transact({'from': bob})
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    
    # save data parameter from the InterledgerEventSending() event
    logs = token_instance.events.InterledgerEventSending().processReceipt(receipt)
    data = logs[0]['args']['data']
    blockNumber = logs[0]['blockNumber']
    
    tx_info = w3.eth.getTransaction(tx_hash)
    gas_used = receipt['gasUsed'] 
    gas_price = int(tx_info ['gasPrice']) * (10**(-9)) # convert to gwei
    cost = gas_price * gas_used * (10**(-9)) # convert to ether
    return (data, blockNumber,gas_used)





def non_blocking_create_token(contract_minter, token_instance, w3, tokenId = None):
    # Create a token
    if(tokenId == None):
        tokenId = uuid4().int
    tokenURI = "weapons/"
    assetName = w3.toBytes(text="Vorpal Sword")

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.mint(w3.eth.accounts[1], tokenId, tokenURI, assetName).transact({'from': contract_minter})
    return (tokenId, tx_hash)


def non_blocking_commit_transaction(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[0]

    tx_hash = token_instance.functions.interledgerCommit(tokenId).transact({'from': bob})
    return tx_hash

def non_blocking_abort_transaction(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[0]
    reason = 4
    tx_hash = token_instance.functions.interledgerAbort(tokenId, reason).transact({'from': bob})
    return tx_hash
def non_blocking_transfer_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.transferOut(tokenId).transact({'from': bob})
    return tx_hash

def non_blocking_accept_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to here 
    bob = w3.eth.accounts[1]
    tx_hash = token_instance.functions.accept(tokenId).transact({'from': contract_minter})
    return tx_hash

def calculate_used_gas(tx_hash,w3):
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    gas_used = receipt['gasUsed'] 
    return gas_used


