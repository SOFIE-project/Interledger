from sofie_asset_transfer.interfaces import ErrorCode
from sofie_asset_transfer.interledger import Transfer
from sofie_asset_transfer.ethereum import Web3Initializer, EthereumInitiator, EthereumResponder
import pytest, time
import asyncio 
import json, time, os
from web3 import Web3

# Set this variable to True to execute these tests
# Remember to have an ethereum instance with mining time *NOT* automatic (like in ganache)
ENABLE_THIS_TESTS = False

# Helper functions
def readContractData(path):
    with open(path) as obj:
        jsn = json.load(obj)
        return jsn["abi"], jsn["bytecode"]


def create_contract(w3, abi, bytecode, _from):

    # Create contract
    TokenContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = TokenContract.constructor("GameToken", "GAME").transact({'from': _from})
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    address = tx_receipt.contractAddress
    token_instance = w3.eth.contract(abi=abi, address=address)
    return token_instance

# current working directory changes if you run pytest in ./, or ./tests/ or ./tests/system
cwd = os.getcwd()
contract_path = "truffle/build/contracts/GameToken.json"

if "system" in cwd.split('/'):
    contract_path = "../../" + contract_path
elif "tests" in cwd.split('/'):
    contract_path = "../" + contract_path
else:
    contract_path = "./" + contract_path

def setUp():

    # Setup web3 and state
    url = "HTTP://127.0.0.1"
    port = 8545
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))

    abi, bytecode = readContractData(contract_path)

    contract_minter = w3.eth.accounts[0]
    bob = w3.eth.accounts[1]

    token_instance = create_contract(w3, abi, bytecode, contract_minter)

    # Create a token
    tokenId = 123
    tokenURI = "weapons/"
    assetId = w3.toBytes(text="Vorpal Sword")

    token_instance.functions.mint(bob, tokenId, tokenURI, assetId).transact({'from': contract_minter})

    t = Transfer()
    t.data = dict()
    t.data["assetId"] = tokenId

    return(contract_minter, token_instance, url, port, t)


@pytest.mark.asyncio
async def test_responder_receive_timeout():

    if not ENABLE_THIS_TESTS:
        return 

    (contract_minter, token_instance, url, port, t) = setUp()

    ### Test Ethereum Responder ###
    
    resp = EthereumResponder(contract_minter, token_instance, url, port=port)
    resp.timeout = 0

    result = await resp.receive_transfer(t)

    assert result["status"] == False
    assert result["error_code"] == ErrorCode.TIMEOUT


#
# Test abort_transfer
#

@pytest.mark.asyncio
async def test_initiator_abort():

    if not ENABLE_THIS_TESTS:
        return

    (contract_minter, token_instance, url, port, t) = setUp()

    ### Test Ethereum Initiator ###
    

    init = EthereumInitiator(contract_minter, token_instance, url, port=port)
    init.timeout = 0

    result = await init.abort_transfer(t)

    assert result["status"] == False
    assert result["error_code"] == ErrorCode.TIMEOUT


#
# Test commit_transfer
#

@pytest.mark.asyncio
async def test_initiator_commit():

    if not ENABLE_THIS_TESTS:
        return

    (contract_minter, token_instance, url, port, t) = setUp()

    ### Test Ethereum Initiator ###
    

    init = EthereumInitiator(contract_minter, token_instance, url, port=port)
    init.timeout = 0

    result = await init.commit_transfer(t)

    assert result["status"] == False
    assert result["error_code"] == ErrorCode.TIMEOUT