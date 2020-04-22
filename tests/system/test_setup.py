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
        (contract_minter, contract_address, contract_abi, url, port, private_key, password) = parse_ethereum(parser, ledger)

    else:
        print(f"WARNING: ledger type {ledger_type} not supported yet")
        exit(1)

    return (contract_minter, contract_address, contract_abi, url, port)


def create_token(contract_minter, token_instance, w3, tokenId = None):
    # Create a token
    if(tokenId == None):
        tokenId = uuid4().int
    tokenURI = "weapons/"
    assetName = w3.toBytes(text="Vorpal Sword")

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.mint(w3.eth.accounts[1], tokenId, tokenURI, assetName).transact({'from': contract_minter})
    w3.eth.waitForTransactionReceipt(tx_hash)
    return tokenId

def accept_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to here 
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.accept(tokenId).transact({'from': contract_minter})
    w3.eth.waitForTransactionReceipt(tx_hash)

def transfer_token(contract_minter, token_instance, w3, tokenId):
    # change state of token to transfer out
    bob = w3.eth.accounts[1]

    tx_hash = token_instance.functions.transferOut(tokenId).transact({'from': bob})
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    
    # save data parameter from the InterledgerEventSending() event
    logs = token_instance.events.InterledgerEventSending().processReceipt(receipt)
    data = logs[0]['args']['data']
    
    return data

