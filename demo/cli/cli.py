from configparser import ConfigParser
from cmd import Cmd
import sys
import time
import json
import random

import web3
from eth_abi import encode_single, decode_single

# CLI app to test Interledger interactively
# The app connects to two ethereum instances, whose connection data are provided 
# by a configuration file, given as a first argument to this script

LEFT_LABEL = "left"
RIGHT_LABEL = "right"

HELP_CMDS = """Available commands (try 'example_run' if unsure what to do):
    - mint <tokenId: int> <tokenURI: str> <assetName: str>
    - transfer_out <ledger: str> <tokenId: int>
    - state_of <tokenId: int>
    - example_run
    - help
    - exit
    - quit"""
    
HELP_LEDGERS = """Available ledgers <ledger>:
    - left
    - right"""

STATE_MAP = {
    0: "Not Here",
    1: "Transfer Out",
    2: "Here"
}

#
# Print functions
#

def print_help():
    # Print the CLI commands
    print(f"{HELP_CMDS}\n\n{HELP_LEDGERS}")
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
def read_contract_abi(path):
    # Read the contract abi, which is necessary for contract object creation

    with open(path) as file:
        data = json.load(file)
        return data


def init_web3(parser, section, label):
    # Initialize web3 for a ledger and return a dictionary with the useful info for that ledger

    endpoint = f"{parser.get(section, 'url')}:{parser.get(section, 'port')}"
    web3_instance = web3.Web3(web3.Web3.HTTPProvider(endpoint))

    if web3_instance.isConnected():

        #print(f"OK - {label}: connected to {endpoint}")
        
        abi_file = parser.get(section, "contract_abi")
        abi = read_contract_abi(abi_file)
    
        ledger = dict()
        ledger["web3"] = web3_instance
        ledger["endpoint"] = endpoint
        ledger["minter"] = parser.get(section, "minter")
        ledger["contract_address"] = parser.get(section, "contract")
        ledger["contract"] = ledger["web3"].eth.contract(abi=abi, 
                                                         address=ledger["contract_address"])

        return ledger
    else:
        print("ERROR Not connected to : ", endpoint)
        sys.exit(1)



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

    #print(f"- Set default account in ledger left: {ledger['endpoint']}")
    #account1 = select_account_from(ledger["web3"].eth.accounts)
    #ledger["user"] = ledger["web3"].toChecksumAddress(account1)
    #print()
    
    # just use the first available account
    ledger["user"] = ledger["web3"].eth.accounts[0]

    return ledger


def send_transaction(ledger: dict, from_address: str, 
                     function_name: str, arguments: list, debug: bool = False):
    """Calls specific smart contract function at ledger with arguments
    
    :param ledger: ledger object to use
    :param from_address: address to use in "from:" field of the transaction
    :param function_name: name of the function to call
    :param arguments: function arguments as a list
    :param debug: wherever to print message about called fuction
    
    :returns: state in case of getStateOfToken call 
    """
    
    # tokenId is second argument for mint, encoded second argument for
    # interledgerReceive, and first argument for other functions
    if function_name == "mint":
        tokenId = arguments[1]
    elif function_name == "interledgerReceive": # tokenId is encoded 
        tokenId = decode_single('uint256', arguments[1])
    else:
        tokenId = arguments[0]
        
    if debug is True:
        print(f"Calling *{function_name}* for tokenId {tokenId} at {ledger['endpoint']}")
    
    try:
        # use call() for getStateOfToken
        if function_name == "getStateOfToken":
            state = ledger["contract"].functions.getStateOfToken(arguments[0]).call()
            return state
        else:
            tx_hash = getattr(ledger["contract"].functions, function_name)(*arguments) \
                .transact({"from": from_address})
            receipt = ledger["web3"].eth.waitForTransactionReceipt(tx_hash)
                
    except web3.exceptions.TimeExhausted as e :
        print(f"Timeout error during {function_name} in {ledger['endpoint']}")

    except ValueError as e:
        d = eval(e.__str__())
        print(f"Contract error during {function_name} in {ledger['endpoint']}: {d['message']}")

    except:
        print(f"General error during {function_name} in {ledger['endpoint']}", sys.exc_info()[0])
        

def setup_ledgers(config_file: str):
    
    parser = ConfigParser()
    parser.read(config_file)
    
    left_section = parser.get('service', LEFT_LABEL)
    right_section = parser.get('service', RIGHT_LABEL)
    
    ledgers = dict()
    ledgers[LEFT_LABEL] = init_web3(parser, left_section, LEFT_LABEL)
    ledgers[RIGHT_LABEL] = init_web3(parser, right_section, RIGHT_LABEL)

    # Set user accounts
    ledgers[LEFT_LABEL] = select_account(ledgers[LEFT_LABEL])
    ledgers[RIGHT_LABEL] = select_account(ledgers[RIGHT_LABEL])
    
    print_user_accounts(ledgers)
    print_help()
    
    return ledgers


class CliDemo(Cmd):
    
    def __init__(self, ledgers: object):
        self.ledgers = ledgers
        self.prompt = 'Type a command> '
        self.allowed_ledgers = {LEFT_LABEL, RIGHT_LABEL}
        self.tokens = {} # store history of tokens
        super(CliDemo, self).__init__()
        
    # override exception handling
    def onecmd(self, line):
        try:
            return super().onecmd(line)
        except:
            print("General error: ", sys.exc_info()[0])
            return False 

    # exit on 'q' input
    def default(self, line):
        if line == 'q':
            return self.do_exit(line)
 
        super().default(line)
    
    def do_exit(self, line):
        '''exit the application.'''
        print("Exiting...")
        return True
    
    def help_exit(self):
        print("Exit the application.")
    
    do_EOF = do_exit
    help_EOF = help_exit
    
    do_quit = do_exit
    help_quit = help_exit
    
    def do_mint(self, line):
        """mint <tokenId: int> <tokenURI: str> <assetName: str>
        
        Mints new token with tokenId, tokenURI and assetName. 
        New token is activated in the left ledger.
        """

        args = line.split()
        
        if len(args) != 3:
            print("mint command needs 3 parameters")
            return
        
        tokenId = int(args[0])
        token_data = encode_single('uint256', tokenId)
        self.tokens[str(tokenId)] = True
        tokenURI = args[1]
        assetName = args[2]
        assetNameBytes = self.ledgers[LEFT_LABEL]["web3"].toBytes(text = assetName)
        
        # Create tokens in both ledgers, and activate token in left ledger
        arguments = (self.ledgers[LEFT_LABEL]["user"], tokenId, tokenURI, assetNameBytes)
        send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                         "mint", arguments, True)

        arguments = (self.ledgers[RIGHT_LABEL]["user"], tokenId, tokenURI, assetNameBytes)
        send_transaction(self.ledgers[RIGHT_LABEL], self.ledgers[RIGHT_LABEL]["minter"], 
                         "mint", arguments, True)
        
        send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                         "interledgerReceive", [1, token_data], True)
        
        # check the state
        state_left = send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                                      "getStateOfToken", [tokenId], True)
        assert state_left == 2
        
        print(f"""Token info:
        - tokenId: {tokenId}
        - URI: {tokenURI}
        - assetName: {assetName}
        - owner_left: {self.ledgers[LEFT_LABEL]["user"]}
        - owner_right: {self.ledgers[RIGHT_LABEL]["user"]}
        - token active in ledger *left*
        """)

        
    def do_transfer_out(self, line):
        """transfer_out <ledger: str> <tokenId: int>
        
        Sets the state of token in specified ledger to \"Transfer Out\".
        This initiates the Interledger process.
        """

        args = line.split()

        if len(args) != 2:
            print("transfer_out command needs 2 parameters")
            return

        ledger_id = args[0]
        if ledger_id not in self.allowed_ledgers:
            print(f"Invalid ledger {ledger_id}, allowed ledgers are: {self.allowed_ledgers}")
            return
        
        ledger = self.ledgers[ledger_id]
        tokenId = int(args[1])
        self.tokens[str(tokenId)] = True
        
        send_transaction(ledger, ledger["user"], "transferOut", [tokenId], True)
        
    def complete_transfer_out(self, text, line, start_index, end_index):
        # show all ledgers in the beginning
        if len(line[:end_index].split()) == 1:
            return [i for i in self.allowed_ledgers]
        
        if len(line[start_index:].split()) > 0:
            current_word = line[start_index:].split()[0]
        else:
            current_word = ""
        
        # valid ledger is already selected
        if current_word in self.allowed_ledgers:
            return
        
        # Only enable ledger autocomplete for first argument 
        if start_index == len("transfer_out") + 1:
            return [i + ' ' for i in self.allowed_ledgers
                    if (i.startswith(current_word) and i is not current_word)]

        first_arg = line.split()[1]
        
        # show all tokens after first argument
        if len(line) == start_index and len(line.split()) == 2:
            return [i for i in self.tokens.keys()]

        # Eable token autocomplete for second argument
        if start_index == len("transfer_out") + len(first_arg) + 2:
            values = []
            for t in self.tokens.keys():
                if t.startswith(current_word):
                    rest_of_line = line[end_index:]
                    if t.endswith(rest_of_line):
                        # handle special case where cursor is within the valid match
                        tmp = t.rfind(rest_of_line)
                        values.append(t[:tmp])
                    else:
                        values.append(t)
            return values


    def do_state_of(self, line):
        """state_of <tokenId: int>
        
        Prints the state of the token in both ledgers.
        """

        args = line.split()

        if len(args) != 1:
            print("state_of command needs 1 parameter")
            return

        tokenId = int(args[0])
        self.tokens[str(tokenId)] = True

        # Read state from ledger
        state_left = send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                                      "getStateOfToken", [tokenId], True)
        state_right = send_transaction(self.ledgers[RIGHT_LABEL], self.ledgers[RIGHT_LABEL]["minter"], 
                                       "getStateOfToken", [tokenId], True)

        # Print the state
        print(f"\nState of {tokenId} in ledger left: *{STATE_MAP[state_left]}*")
        print(f"State of {tokenId} in ledger right: *{STATE_MAP[state_right]}*\n")
        
    def complete_state_of(self, text, line, start_index, end_index):
        # show all tokens in the beginning
        if len(line) == start_index and len(line.split()) == 1:
            return [i for i in self.tokens.keys()]

        if len(line[start_index:].split()) > 0:
            current_word = line[start_index:].split()[0]
        else:
            current_word = ""

        # valid token is already selected
        if int(current_word) in self.tokens.keys():
            return

        # Only enable autocomplete for first argument
        if start_index is len("state_of") + 1:
            values = []
            for t in self.tokens.keys():
                if t.startswith(current_word):
                    rest_of_line = line[end_index:]
                    if t.endswith(rest_of_line):
                        # handle special case where cursor is within the valid match
                        tmp = t.rfind(rest_of_line)
                        values.append(t[:tmp])
                    else:
                        values.append(t)
            return values

    
    def do_example_run(self, line):
        """example_run
            
        Runs an example consisting of:
        1. Minting tokens in both ledgers
        2. Activating token in left ledger
        3. Calling transfer_out on token in left ledger
        4. Waits until the Interledger process completes
        
        At the end of example the token should be transferred by Interledger to right ledger,
        token's state will be: \"Here\" in right ledger and \"Not Here\" in left ledger.
        """

        tokenId = random.randrange(1, 2**32)
        token_data = encode_single('uint256', tokenId)
        self.tokens[str(tokenId)] = True

        tokenURI = "weapons/"
        assetName = "Sword"
        assetNameBytes = self.ledgers[LEFT_LABEL]["web3"].toBytes(text = assetName)

        
        print(f"Minting new token with id {tokenId} in both ledgers...")
        arguments = (self.ledgers[LEFT_LABEL]["user"], tokenId, tokenURI, assetNameBytes)
        send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                         "mint", arguments)

        arguments = (self.ledgers[RIGHT_LABEL]["user"], tokenId, tokenURI, assetNameBytes)
        send_transaction(self.ledgers[RIGHT_LABEL], self.ledgers[RIGHT_LABEL]["minter"], 
                         "mint", arguments)
                
        time.sleep(1)
            
        state_left = send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                                      "getStateOfToken", [tokenId])
        state_right = send_transaction(self.ledgers[RIGHT_LABEL], self.ledgers[RIGHT_LABEL]["minter"], 
                                       "getStateOfToken", [tokenId])
        print(f"\tState of token {tokenId} in ledger left: *{STATE_MAP[state_left]}*")
        print(f"\tState of token {tokenId} in ledger right: *{STATE_MAP[state_right]}*")

            
        print("\nActivating token in left ledger...")
        send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["minter"], 
                         "interledgerReceive", [1, token_data])


        time.sleep(1)

        state_left = send_transaction(self.ledgers[LEFT_LABEL], 
                                      self.ledgers[LEFT_LABEL]["minter"], 
                                      "getStateOfToken", [tokenId])
        state_right = send_transaction(self.ledgers[RIGHT_LABEL], 
                                       self.ledgers[RIGHT_LABEL]["minter"], 
                                       "getStateOfToken", [tokenId])
        print(f"\tState of token {tokenId} in ledger left: *{STATE_MAP[state_left]}*")
        print(f"\tState of token {tokenId} in ledger right: *{STATE_MAP[state_right]}*")


        print("\nCalling transfer_out for token in left ledger...")
        send_transaction(self.ledgers[LEFT_LABEL], self.ledgers[LEFT_LABEL]["user"], 
                         "transferOut", [tokenId])

        #time.sleep(1)
        
        state_left = send_transaction(self.ledgers[LEFT_LABEL], 
                                      self.ledgers[LEFT_LABEL]["minter"], 
                                      "getStateOfToken", [tokenId])
        state_right = send_transaction(self.ledgers[RIGHT_LABEL], 
                                       self.ledgers[RIGHT_LABEL]["minter"], 
                                       "getStateOfToken", [tokenId])
        print(f"\tState of token {tokenId} in ledger left: *{STATE_MAP[state_left]}*")
        print(f"\tState of token {tokenId} in ledger right: *{STATE_MAP[state_right]}*")
        
        
        print("\nWaiting until Interledger process completes...")    
        # it might take some time before the Interledger process completes
        while True:
            state_left = send_transaction(self.ledgers[LEFT_LABEL], 
                                          self.ledgers[LEFT_LABEL]["minter"], 
                                          "getStateOfToken", [tokenId])
            if state_left == 0:
                break
            time.sleep(1)
            
        state_right = send_transaction(self.ledgers[RIGHT_LABEL], 
                                       self.ledgers[RIGHT_LABEL]["minter"], 
                                       "getStateOfToken", [tokenId])
        print(f"\tState of token {tokenId} in ledger left: *{STATE_MAP[state_left]}*")
        print(f"\tState of token {tokenId} in ledger right: *{STATE_MAP[state_right]}*")
        

def main():
    if len(sys.argv) <= 1:
        print("ERROR: Provide a *.cfg config file as an argument to run the demo")
        sys.exit(1)
        
    ledgers = setup_ledgers(sys.argv[1])
    CliDemo(ledgers).cmdloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n--- Quitting Demo after interruption from keyboard ---")
