from configparser import ConfigParser
from src.sofie_asset_transfer.interledger import Interledger
from src.sofie_asset_transfer.ethereum import EthereumInitiator, EthereumResponder
import sys, json, asyncio
from web3 import Web3

tokenContractFile = "truffle/build/contracts/GameToken.json"

# Helper function to read Ethereum related options from configuration file
def get_ethereum_data(parser, section):
    # Read data
    url = parser.get(section, 'url')
    port = parser.get(section, 'port')
    path = url + ':' + port
    minter = parser.get(section, 'minter')
    address = parser.get(section, 'contract') 
    abi = ""
    with open(tokenContractFile) as obj:
        jsn = json.load(obj)
        abi = jsn["abi"]

    # Init web3
    web3 = Web3(Web3.HTTPProvider(path))
    # Get contract
    contract = web3.eth.contract(abi=abi, address=address)

    return (minter, contract, url, port)


# Helper function to build a left to right interledger
def left_to_right_bridge(parser, left, right):

    initiator = None
    responder = None
    ledger_left = parser.get(left, 'type')
    ledger_right = parser.get(right, 'type')

    # Left ledger
    if ledger_left == "ethereum":
        (minter, contract, url, port) = get_ethereum_data(parser, left)
        # Create Initiator
        initiator = EthereumInitiator(minter, contract, url, port)

    elif ledger_left == "OTHER":
        print("WARNING: ledger type not supported yet")
        exit(1)
    
    # Right ledger
    if ledger_right == "ethereum":
        (minter, contract, url, port) = get_ethereum_data(parser, right)
        # Create Responder
        responder = EthereumResponder(minter, contract, url, port)

    elif ledger_right == "OTHER":
        print("WARNING: ledger type not supported yet")
        exit(1)

    return (initiator, responder)


# Helper function to build a right to left interledger
def right_to_left_bridge(parser, left, right):

    initiator = None
    responder = None
    ledger_left = parser.get(left, 'type')
    ledger_right = parser.get(right, 'type')
    
    # Right ledger
    if ledger_right == "ethereum":
        (minter, contract, url, port) = get_ethereum_data(parser, right)
        # Create Initiator
        initiator = EthereumInitiator(minter, contract, url, port)

    else :
        print("WARNING: ledger type not supported yet")
        exit(1)

    # Left ledger
    if ledger_left == "ethereum":
        (minter, contract, url, port) = get_ethereum_data(parser, left)
        # Create Responder
        responder = EthereumResponder(minter, contract, url, port)

    else :
        print("WARNING: ledger type not supported yet")
        exit(1)

    return (initiator, responder)


def main():
    
    # Parse command line iput 
    if len(sys.argv) <= 1:
        print("WARNING: Provide a *.cfg config file to initialize Interledger")
        exit(1)

    parser = ConfigParser()
    parser.read(sys.argv[1])


    # Get direction
    direction = parser.get('service', 'direction')
    left = parser.get('service', 'left')
    right = parser.get('service', 'right')


    # Build interledger bridge(s)
    interledger_left_to_right = None
    interledger_right_to_left = None

    if direction == "left-to-right":
        
        (initiator, responder) = left_to_right_bridge(parser, left, right)

        interledger_left_to_right = Interledger(initiator, responder)


    elif direction == "right-to-left":

        (initiator, responder) = right_to_left_bridge(parser, left, right)

        interledger_right_to_left = Interledger(initiator, responder)

    elif direction == "both":

        (initiator_lr, responder_lr) = left_to_right_bridge(parser, left, right)
        (initiator_rl, responder_rl) = right_to_left_bridge(parser, left, right)

        interledger_left_to_right = Interledger(initiator_lr, responder_lr)
        interledger_right_to_left = Interledger(initiator_rl, responder_rl)

    else:
        print("WARNING: supported 'direction' values are 'left-to-right', 'right-to-left' and 'both'")


    # Init Interledger(s)
    task = None

    if interledger_left_to_right and interledger_right_to_left:

        future_left_to_right = asyncio.ensure_future(interledger_left_to_right.run())
        future_right_to_left = asyncio.ensure_future(interledger_right_to_left.run())

        task = asyncio.gather(future_left_to_right, future_right_to_left)
        print("Starting running routine for *double* sided interledger")

    elif interledger_left_to_right:

        task = asyncio.ensure_future(interledger_left_to_right.run())
        print("Starting running routine for *left to right* interledger")

    elif interledger_right_to_left:

        task = asyncio.ensure_future(interledger_right_to_left.run())
        print("Starting running routine for *right to left* interledger")

    else:

        print("ERROR while creating tasks for interledger")
        exit(1)
    
    return (task, interledger_left_to_right, interledger_right_to_left)

if __name__ == "__main__":

    (task, interledger1, interledger2) = main()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(task)

    except KeyboardInterrupt as e:
        print("-- Interrupted by keyword --")

        if interledger1: 
            interledger1.stop()
        if interledger2:
            interledger2.stop()

        loop.run_until_complete(task)
        loop.close()

        print("-- Finished correctly --")