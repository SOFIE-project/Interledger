from configparser import ConfigParser
from enum import Enum, auto
from sys import argv
from web3 import Web3
import json

# CLI app to test Interledger interactively
# The app connects to two ethereum instances, 
# whose connection data are provided by a configuration file, 
# a main argument of this script

#
#CLI commands
#

help_cmds = """Available commands:
- mint <tokenId: int> <tokenURI: str> <assetId: str>
- transfer_out <direction> <tokenId: int>
- state_of <tokenId>
- set_accounts
- accounts
- help
- quit"""
help_directions = """Available <direction> directions:
- left
- right"""

#
# Printing functions
#

def print_help():
    # Print the CLI commands
    print("------")
    print(f"{help_cmds}\n{help_directions}")
    print("------")


def print_accounts(ledger1, ledger2):
    # Print the accounts available in each ledger

    print(f"Accounts at {ledger1['endpoint']}:")
    for (index, account) in enumerate(ledger1['web3'].eth.accounts):
        print(f"{index}) {account}")
    print()
    print(f"Accounts at {ledger2['endpoint']}:")
    for (index, account) in enumerate(ledger2['web3'].eth.accounts):
        print(f"{index}) {account}")


def print_user_accounts(ledgers):
    # Print the accounts of the user in both ledgers

    print()
    print(f"""Your accounts:
    Left ledger, {ledgers['left']['endpoint']}: {ledgers['left']['user']}
    Right ledger, {ledgers['right']['endpoint']}: {ledgers['right']['user']}
    """)


#
# Utility functions
#

def read_contract(path):
    # Read the contract data useful for contract object creation

    with open(path) as file:
        data = json.load(file)
        return data["abi"], data["bytecode"]


def init_web3(parser, section, label):
    # Initialize web3 for a ledger and return a dictionary with the useful info for that ledger

    ledger = dict()
    url = parser.get(section, 'url')
    port = parser.get(section, 'port')
    endpoint = f"{url}:{port}"
    abi, bytecode = read_contract("./truffle/build/contracts/GameToken.json")
    
    ledger["web3"] = Web3(Web3.HTTPProvider(endpoint))

    if ledger["web3"].isConnected():
        print(f"OK - {label}: connected to {endpoint}")
    else:
        print("WARNING Not connected to : ", endpoint)
        exit(1)

    ledger["endpoint"] = endpoint
    ledger["minter"] = parser.get(section, "minter")
    ledger["user"] = parser.get(section, 'user')
    ledger["contract_address"] = parser.get(section, "contract")
    ledger["contract"] = ledger["web3"].eth.contract(abi=abi, address=ledger["contract_address"])

    return ledger


def select_account_from(accounts):
    # Print and select an account from those provided a ledger 

    for (index, account) in enumerate(accounts):
        print(f"{index}) {account}")

    print("- Type the index: ")
    idx = int(input(")> "))

    while idx not in range(0, len(accounts)):

        print("Wrong index")
        idx = int(input(")> "))

    return accounts[idx]
    

def select_accounts(ledgers):
    # For both ledgers call select_accoun_from and store the chosed account
    # is necessary to call web3.toCheckssumAddress, otherwise web3 will raise errors
    
    print(f"- Set default account in ledger left: {ledgers['left']['endpoint']}")
    account1 = select_account_from(ledgers['left']["web3"].eth.accounts)
    ledgers["left"]["user"] = ledgers['left']["web3"].toChecksumAddress(account1)
    print()
    print(f"- Set default account in ledger right: {ledgers['right']['endpoint']}")
    account1 = select_account_from(ledgers['right']["web3"].eth.accounts)
    ledgers["right"]["user"] = ledgers['right']["web3"].toChecksumAddress(account1)

    return ledgers



def main():

    print("-- Starting CLI client for interledger -- ")

    # Input
    class Cli_input(Enum):
        CONFIG = auto()
        INPUT_LEN = auto()

    if len(argv) < Cli_input.INPUT_LEN.value:
        print("WARNING, usage: python3 cli.py <address_ledger_1>")
        exit(1)


    # Read config file and create ledgers
    parser = ConfigParser()
    parser.read(argv[Cli_input.CONFIG.value])
    left = parser.get('service', 'left')
    right = parser.get('service', 'right')

    print("- Connecting to ledgers")
    ledgers = dict()
    ledgers["left"] = init_web3(parser, left, "left")
    ledgers["right"] = init_web3(parser, right, "right")
    print()

    # Set default accounts ledger 1 and ledger 2
    ledgers = select_accounts(ledgers)
    
    # Start loop 
    print_user_accounts(ledgers)
    print("------")
    print_help()

    while True:

        print("""Type a command:""")
        cmd = input(")> ")
        
        keywords = cmd.split()
        cmd = keywords[0]
        
        if cmd == "mint":
            tokenId = int(keywords[1])
            tokenURI = keywords[2]
            assetId = keywords[3]
            to_left = ledgers["left"]["user"]
            to_right = ledgers["right"]["user"]
            

            # Create token in left and right ledgers
            ledger = ledgers["left"]
            assetIdBytes = ledger["web3"].toBytes(text=assetId)
            tx = ledger["contract"].functions.mint(to_left, tokenId, tokenURI, assetIdBytes).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

            ledger = ledgers["right"]
            tx = ledger["contract"].functions.mint(to_right, tokenId, tokenURI, assetIdBytes).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

            # activate the token (by default, it is not active) in ledger right
            tx = ledger["contract"].functions.accept(tokenId).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

            print(f"""Token info:
            - tokenId: {tokenId}
            - URI: {tokenURI}
            - assetId: {assetId}
            - owner_left: {to_left}
            - owner_right: {to_right}
            - token active in ledger *right*
            """)


        elif cmd == "transfer_out":
            ledger_id = keywords[1]
            tokenId = int(keywords[2])
            ledger = ledgers[ledger_id]

            print(ledger["user"])

            tx = ledger["contract"].functions.transferOut(tokenId).transact({"from": ledger["user"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)
            print(f"Transfer request from user {ledger['user']} of token {tokenId}: leaving ledger {ledger_id}")
            # Interledger will work in this step ...

        elif cmd == "state_of":
            tokenId = int(keywords[1])         

            state_left = ledgers["left"]["contract"].functions.getStateOfToken(tokenId).call()
            state_right = ledgers["right"]["contract"].functions.getStateOfToken(tokenId).call()

            statesMap = {
                0: "Here",
                1: "Transfer Out",
                2: "Not Here"
            }

            if state_left == 0 and state_right == 0:
                # TODO FIXME from solidity default non existing value is 0
                # so not existing assets return state = 0, which is "here"
                # FIXME also in solidity
                state_left = 2
                state_right = 2


            print(f"State of {tokenId} in ledger left: *{statesMap[state_left]}*")
            print(f"State of {tokenId} in ledger right: *{statesMap[state_right]}*")


        elif cmd == "help":
            print("------")
            print_user_accounts(ledgers)
            print_help()


        elif cmd == "accounts":
            print_accounts(ledgers["left"], ledgers["right"])


        elif cmd == "set_accounts":
            ledgers = select_accounts(ledgers)
            print("------")
            print_user_accounts(ledgers)
            print("------")


        elif cmd == "quit":
            print("-- Quitting CLI --")
            break

        else:
            print("Invalid command")



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("--- Quitting CLI after interruption from keyboard ---")