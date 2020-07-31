from configparser import ConfigParser
from data_transfer.interfaces import ErrorCode
from data_transfer.interledger import Transfer
from data_transfer.ksi import KSIResponder
from .test_setup import setUp_ksi
import pytest, asyncio
import os, json
import web3
import requests
from web3 import Web3

# # # Local view
# #
# #  EthereumResponder -> Ledger
#
# # 
#

def test_init(config):

    (url, hash_algorithm, username, password) = setUp_ksi(config)
    resp = KSIResponder(url, hash_algorithm, username, password)

    assert resp.url == url
    assert resp.hash_algorithm == hash_algorithm
    assert resp.username == username
    assert resp.password == password
    
#
# Test receive_transfer
#



@pytest.mark.asyncio
async def test_responder_receive(config):

    (url, hash_algorithm, username, password) = setUp_ksi(config)

    ### Test Ethereum Responder ###

    resp = KSIResponder(url, hash_algorithm, username, password)

    nonce, data = "42", b'dummy'
    result = await resp.send_data(nonce, data)
    
    url = resp.url + "/" + result["tx_hash"]
    # send it as a GET request and check for the result
    ksi_request = requests.get(url, auth=(resp.username, resp.password))

    assert ksi_request.json()['verificationResult']['status'] == "OK"

    assert ksi_request.status_code == 200
    assert result["status"] == True


@pytest.mark.asyncio
async def test_responder_receive_wrong_hash_algorithm(config):

    (url, hash_algorithm, username, password) = setUp_ksi(config)

    ### Test Ethereum Responder ###

    resp = KSIResponder(url, hash_algorithm, username, password)
    resp.hash_algorithm = 'dummy'
    nonce, data = "42", b'dummy'
    result = await resp.send_data(nonce, data)
    
    assert result["status"] == False
    assert result["error_code"] == ErrorCode.UNSUPPORTED_KSI_HASH

