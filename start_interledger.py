import sys, json, asyncio
from web3 import Web3
from configparser import ConfigParser

from src.data_transfer.interledger import Interledger
from src.data_transfer.ethereum import EthereumInitiator, EthereumResponder
from src.data_transfer.ksi import KSIResponder
from src.data_transfer.fabric import FabricInitiator, FabricResponder


# Helper function to read Ethereum related options from configuration file
def parse_ethereum(parser, section):
    net_type = parser.get(section, 'type')
    assert net_type == 'ethereum'

    url = parser.get(section, 'url')
    port = None
    try:
        port = parser.get(section, 'port')
    except:
        pass
    path = url
    if port:
        path += ':' + str(port)
    minter = Web3.toChecksumAddress(parser.get(section, 'minter'))
    contract_address = Web3.toChecksumAddress(parser.get(section, 'contract'))
    abi_file = parser.get(section, 'contract_abi')
    contract_abi = ''
    try:
        with open(abi_file) as json_file:
            contract_abi = json.load(json_file)
    except:
        print("ERROR parsing smart contract ABI file for:", section , ". Error:", sys.exc_info()[0])
        exit(-1)
    private_key = None
    try:
        private_key = parser.get(section, 'private_key')
    except:
        pass
    
    password = None
    try:
        password = parser.get(section, 'password')
    except:
        pass

    poa = None
    try:
        poa = parser.get(section, 'poa') in ('true', 'True')
    except:
        pass

    return (minter, contract_address, contract_abi, url, port, private_key, password, poa)

# Helper function to read KSI related options from configuration file
def parse_ksi(parser, section):
    net_type = parser.get(section, 'type')
    assert net_type == 'ksi'
    
    # Read data
    url = parser.get(section, 'url')
    hash_algorithm = parser.get(section, 'hash_algorithm')
    username = parser.get(section, 'username')
    password = parser.get(section, 'password')
    
    return (url, hash_algorithm, username, password)


# Helper function to read HyperLedger Fabric related options from configuration file
def parse_fabric(parser, section):
    net_type = parser.get(section, 'type')
    assert net_type == 'fabric'

    # Read data
    net_profile = parser.get(section, 'network_profile')
    channel_name = parser.get(section, 'channel_name')
    cc_name = parser.get(section, 'cc_name')
    cc_version = parser.get(section, 'cc_version')
    org_name = parser.get(section, 'org_name')
    user_name = parser.get(section, 'user_name')
    peer_name = parser.get(section, 'peer_name')

    return (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

# Helper function to build a left to right interledger
# Note: KSI is only supported as destination ledger
def left_to_right_bridge(parser, left, right):

    initiator = None
    responder = None
    ledger_left = parser.get(left, 'type')
    ledger_right = parser.get(right, 'type')

    # Left ledger with initiator
    if ledger_left == "ethereum":
        (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, left)
        # Create Initiator
        initiator = EthereumInitiator(minter, contract_address, contract_abi, url, port, private_key, password, poa)

    elif ledger_left == "fabric":
        (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, left)
        # Create Initiator
        initiator = FabricInitiator(net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    else:
        print(f"ERROR: ledger type {ledger_left} not supported yet")
        exit(1)
    
    # Right ledger with responder
    if ledger_right == "ethereum":
        (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, right)
        # Create Responder
        responder = EthereumResponder(minter, contract_address, contract_abi, url, port, private_key, password, poa)
        
    elif ledger_right == "ksi":
        (url, hash_algorithm, username, password) = parse_ksi(parser, right)
        # Create Responder
        responder = KSIResponder(url, hash_algorithm, username, password)

    elif ledger_right == "fabric":
        (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, left)
        # Create Responder
        responder = FabricResponder(net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    else:
        print(f"ERROR: ledger type {ledger_right} not supported yet")
        exit(1)

    return (initiator, responder)


# Helper function to build a right to left interledger
# Note: KSI is only supported as destination ledger
def right_to_left_bridge(parser, left, right):

    initiator = None
    responder = None
    ledger_left = parser.get(left, 'type')
    ledger_right = parser.get(right, 'type')
    
    # Right ledger with initiator
    if ledger_right == "ethereum":
        (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, right)
        # Create Initiator
        initiator = EthereumInitiator(minter, contract_address, contract_abi, url, port, private_key, password, poa)

    elif ledger_right == "fabric":
        (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, left)
        # Create Initiator
        initiator = FabricInitiator(net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    else :
        print(f"ERROR: ledger type {ledger_right} not supported yet")
        exit(1)

    # Left ledger with Responder
    if ledger_left == "ethereum":
        (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, left)
        # Create Responder
        responder = EthereumResponder(minter, contract_address, contract_abi, url, port, private_key, password, poa)
        
    elif ledger_left == "ksi":
        (url, hash_algorithm, username, password) = parse_ksi(parser, left)
        responder = KSIResponder(url, hash_algorithm, username, password)

    elif ledger_left == "fabric":
        (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, left)
        # Create Responder
        responder = FabricResponder(net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    else :
        print(f"ERROR: ledger type {ledger_left} not supported yet")
        exit(1)

    return (initiator, responder)


def main():
    
    # Parse command line iput 
    if len(sys.argv) <= 1:
        print("ERROR: Provide a *.cfg config file to initialize Interledger")
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
        print("ERROR: supported 'direction' values are 'left-to-right', 'right-to-left' or 'both'")
        print("Check your configuration file")
        exit(1)

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
