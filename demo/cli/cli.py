from configparser import ConfigParser
from enum import Enum, auto
from sys import argv
from web3 import Web3
import json

# CLI app to test Interledger interactively
# The app connects to two ethereum instances, 
# whose connection data are provided by a configuration file, 
# a main argument of this script

LEFT_LABEL = "left"
RIGHT_LABEL = "right"
CONTRACT_PATH = "./truffle/build/contracts/GameToken.json"

HELP_CMDS = """Available commands:
    - mint <tokenId: int> <tokenURI: str> <assetName: str>
    - transfer_out <direction> <tokenId: int>
    - state_of <tokenId>
    - help
    - quit"""
HELP_DIRECTIONS = """Available directions <direction>:
    - left
    - right"""

#
# Print functions
#

def print_help():
    # Print the CLI commands
    print()
    print(f"{HELP_CMDS}\n{HELP_DIRECTIONS}")
    print()


def print_accounts(ledger):
    # Print the accounts available in a ledger

    print(f"Accounts at {ledger['endpoint']}:")
    for (index, account) in enumerate(ledger['web3'].eth.accounts):
        print(f"{index}) {account}")


def print_user_accounts(ledgers):
    # Print the accounts of the user in both ledgers

    print()
    print(f"""Your accounts:
    Left ledger, {ledgers[LEFT_LABEL]['endpoint']}: {ledgers[LEFT_LABEL]['user']}
    Right ledger, {ledgers[RIGHT_LABEL]['endpoint']}: {ledgers[RIGHT_LABEL]['user']}
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

    endpoint = f"{parser.get(section, 'url')}:{parser.get(section, 'port')}"
    web3 = Web3(Web3.HTTPProvider(endpoint))

    if web3.isConnected():

        print(f"OK - {label}: connected to {endpoint}")
        abi, bytecode = read_contract(CONTRACT_PATH)
    
        ledger = dict()
        ledger["web3"] = web3
        ledger["endpoint"] = endpoint
        ledger["minter"] = parser.get(section, "minter")
        ledger["user"] = parser.get(section, 'user')
        ledger["contract_address"] = parser.get(section, "contract")
        ledger["contract"] = ledger["web3"].eth.contract(abi=abi, address=ledger["contract_address"])

        return ledger
    else:
        print("WARNING Not connected to : ", endpoint)
        exit(1)



def select_account_from(accounts):
    # Print and select an account from those provided a ledger 
    # Loop until the index is correct

    for (index, account) in enumerate(accounts):
        print(f"{index}) {account}")

    idx = int(input("Type the index in 0-9)> "))

    while idx not in range(0, len(accounts)):
        print("Wrong index, must be in 0-9")
        idx = int(input("Type the index in 0-9)> "))

    return accounts[idx]
    
def select_account(ledger):
    # Set the user account for the input ledger
    # is necessary to call web3.toCheckssumAddress, otherwise web3 will raise errors

    print(f"- Set default account in ledger left: {ledger['endpoint']}")
    account1 = select_account_from(ledger["web3"].eth.accounts)
    ledger["user"] = ledger["web3"].toChecksumAddress(account1)
    print()

    return ledger



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
    print("- Connecting to ledgers")
    parser = ConfigParser()
    parser.read(argv[Cli_input.CONFIG.value])
    left_section = parser.get('service', LEFT_LABEL)
    right_section = parser.get('service', RIGHT_LABEL)

    ledgers = dict()
    ledgers[LEFT_LABEL] = init_web3(parser, left_section, LEFT_LABEL)
    ledgers[RIGHT_LABEL] = init_web3(parser, right_section, RIGHT_LABEL)

    # Set user accounts ledger 1 and ledger 2
    print()
    ledgers[LEFT_LABEL] = select_account(ledgers[LEFT_LABEL])
    ledgers[RIGHT_LABEL] = select_account(ledgers[RIGHT_LABEL])
    
    # Start loop 
    print_user_accounts(ledgers)
    print_help()

    while True:

        cmd = input("Type a command)> ")
        
        keywords = cmd.split()
        cmd = keywords[0]
        
        if cmd == "mint":
            
            if len(keywords) is not 4:
                print("mint command needs 3 parameters")
                continue

            tokenId = int(keywords[1])
            tokenURI = keywords[2]
            assetName = keywords[3]
            to_left = ledgers[LEFT_LABEL]["user"]
            to_right = ledgers[RIGHT_LABEL]["user"]
            

            # Create token
                # Left ledger
            ledger = ledgers[LEFT_LABEL]
            assetNameBytes = ledger["web3"].toBytes(text=assetName)
            tx = ledger["contract"].functions.mint(to_left, tokenId, tokenURI, assetNameBytes).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

                # Right ledger
            ledger = ledgers[RIGHT_LABEL]
            tx = ledger["contract"].functions.mint(to_right, tokenId, tokenURI, assetNameBytes).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

            # activate the token in ledger right (by default, it is not active)
                # Simulation goals
            tx = ledger["contract"].functions.accept(tokenId).transact({"from": ledger["minter"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)

            print(f"""Token info:
            - tokenId: {tokenId}
            - URI: {tokenURI}
            - assetName: {assetName}
            - owner_left: {to_left}
            - owner_right: {to_right}
            - token active in ledger *right*
            """)


        elif cmd == "transfer_out":

            if len(keywords) is not 3:
                print("transfer_out command needs 2 parameters")
                continue

            ledger_id = keywords[1]
            tokenId = int(keywords[2])
            ledger = ledgers[ledger_id]

            tx = ledger["contract"].functions.transferOut(tokenId).transact({"from": ledger["user"]})
            rcpt = ledger["web3"].eth.waitForTransactionReceipt(tx)
            print(f"Transfer request from user {ledger['user']} of token {tokenId}: leaving ledger {ledger_id}")
            # Interledger will work in this step ...

        elif cmd == "state_of":

            if len(keywords) is not 2:
                print("state_of command needs 1 parameter")
                continue

            tokenId = int(keywords[1])         

            # Read state from ledger
            state_left = ledgers[LEFT_LABEL]["contract"].functions.getStateOfToken(tokenId).call()
            state_right = ledgers[RIGHT_LABEL]["contract"].functions.getStateOfToken(tokenId).call()

            # Print
            statesMap = {
                0: "Not Here",
                1: "Transfer Out",
                2: "Here"
            }

            print(f"State of {tokenId} in ledger left: *{statesMap[state_left]}*")
            print(f"State of {tokenId} in ledger right: *{statesMap[state_right]}*")


        elif cmd == "help":
            print_user_accounts(ledgers)
            print_help()


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