import time, asyncio
from typing import List
import web3
from web3 import Web3

from .interfaces import Initiator, Responder, ErrorCode, LedgerType
from .interledger import Transfer


# Web3 util
class Web3Initializer:
    """This provides proper web3 wrapper for a component
    """
    def __init__(self, url: str, port=None):
        protocol = url.split(":")[0].lower()
        path = url
        if port:
            path += ':' + str(port)
        if protocol in ("http", "https"):
            self.web3 = Web3(Web3.HTTPProvider(path))
        elif protocol == "wss":
            self.web3 = Web3(Web3.WebsocketProvider(path))
        else:
            raise ValueError("Unsupported Web3 protocol")

    def isUnlocked(self, account):
        try:
            self.web3.eth.sign(account, 1)
        except Exception as e:
            return False
        return True


# Initiator implementation
class EthereumInitiator(Web3Initializer, Initiator):
    """Ethereum implementation of the Initiator.
    """
    def __init__(self, minter: str, contract_address: str, contract_abi: object, 
                 url: str, port: int = None, private_key: str = None, password: str = None):
        """
        :param str minter: The contract minter who is in charge of data emiting and committing the status of the data transfer
        :param str contract_address: The address of data transfer contract implementing Interledger interface 
        :param object contract_abi: Contract ABI
        :param str url: The web3 url
        :param int port: The web3 port, if any (default=None) 
        """
        Web3Initializer.__init__(self, url, port)
        self.contract = self.web3.eth.contract(abi=contract_abi, address=contract_address)
        self.last_block = self.web3.eth.blockNumber
        self.private_key = private_key
        self.minter = minter
        self.password = password
        self.timeout = 120
        self.ledger_type = LedgerType.ETHEREUM

    # Initiator functions
    async def listen_for_events(self) -> list:
        """Listen for events fired by the Initiator injected contract stored in the connected Ethereum network.

        :returns: The event transfer lists
        :rtype: list
        """
        # Needs to be blocking
        while True :
            # Create event filter for the event to pay attention to
            filt = self.contract \
                    .events.InterledgerEventSending() \
                    .createFilter(fromBlock=self.last_block+1) # +1 otherwise gets again older block
            entries = filt.get_all_entries()
            if len(entries) == 0:
                await asyncio.sleep(1)
                entries = filt.get_all_entries()
            # update block number
            self.last_block = self.web3.eth.blockNumber
            # Transform entries in Transfer object
            return self._buffer_data(entries)

    async def commit_sending(self, id: str, data: bytes = None) -> bool:
        """Initiate the commit operation to the connected ledger.

        :param str id: the identifier in the originating ledger for a data item
        :param bytes data: optional data to be passed to interledgerCommit() in smart contract

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        tx_hash = None
        try:
            if self.private_key and not self.isUnlocked(self.minter): # needs to unlock with private key
                if data: # pass data to interledgerCommit if it is available
                    transaction = self.contract.functions \
                        .interledgerCommit(Web3.toInt(text=id), data) \
                        .buildTransaction({'from': self.minter})
                else:
                    transaction = self.contract.functions \
                        .interledgerCommit(Web3.toInt(text=id)) \
                        .buildTransaction({'from': self.minter})
                transaction.update({'nonce': self.web3.eth.getTransactionCount(self.minter)})
                signed_tx = self.web3.eth.account.signTransaction(transaction, self.private_key)
                tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            else:
                if data: # pass data to interledgerCommit if it is available
                    tx_hash = self.contract.functions \
                        .interledgerCommit(Web3.toInt(text=id), data) \
                        .transact({'from': self.minter}) # type uint256 required for id in the smart contract
                else:
                    tx_hash = self.contract.functions \
                        .interledgerCommit(Web3.toInt(text=id)) \
                        .transact({'from': self.minter}) # type uint256 required for id in the smart contract
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, timeout=self.timeout)

            if tx_receipt['status']:
                return {"status": True}
            else:
                # TODO search: #tx_receipt
                return {"status": False, 
                        "error_code": ErrorCode.TRANSACTION_FAILURE,
                        "message": "Error in the transaction",
                        "tx_hash": tx_hash}
        except web3.exceptions.TimeExhausted as e:
            # Raised by web3.eth.waitForTransactionReceipt
            return {"status": False, 
                    "error_code": ErrorCode.TIMEOUT,
                    "message": "Timeout after sending the transaction",
                    "tx_hash": tx_hash,
                    "exception": e}
        except ValueError as e:
            # Raised by a contract function 
            d = eval(e.__str__())
            return {"status": False, 
                    "error_code": ErrorCode.TRANSACTION_FAILURE, 
                    "message": d['message'],
                    "tx_hash": tx_hash,
                    "exception": e}

    async def abort_sending(self, id: str, reason: int) -> bool:
        """Initiate the abort operation to the connected ledger.

        :param object transfer: the transfer to abort

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        tx_hash = None
        try:
            if self.private_key and not self.isUnlocked(self.minter): # needs to unlock with private key
                transaction = self.contract.functions \
                    .interledgerAbort(Web3.toInt(text=id), reason) \
                    .buildTransaction({'from': self.minter})
                transaction.update({'nonce': self.web3.eth.getTransactionCount(self.minter)})
                signed_tx = self.web3.eth.account.signTransaction(transaction, self.private_key)
                tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            else:
                tx_hash = self.contract.functions \
                    .interledgerAbort(Web3.toInt(text=id), reason) \
                    .transact({'from': self.minter}) # type uint256 required for id in the smart contract
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, timeout=self.timeout)

            if tx_receipt['status']:            
                return {"status": True,
                        "tx_hash": tx_hash}
            else:
                # TODO search: #tx_receipt
                return {"status": False,
                        "error_code": ErrorCode.TRANSACTION_FAILURE,
                        "message": "Error in the transaction",
                        "tx_hash": tx_hash}
        except web3.exceptions.TimeExhausted as e:
            # Raised by web3.eth.waitForTransactionReceipt
            return {"status": False, 
                    "error_code": ErrorCode.TIMEOUT,
                    "message": "Timeout after sending the transaction",
                    "tx_hash": tx_hash,
                    "exception": e}
        except ValueError as e:
            # Raised by a contract function 
            d = eval(e.__str__())
            return {"status": False, 
                    "error_code": ErrorCode.TRANSACTION_FAILURE, 
                    "message": d['message'],
                    "exception": e}

    # Helper function
    def _buffer_data(self, entries: list):
        """Helper function to create a list of Transfer object from a list of web3 event entries
        """
        transfers = []
        for entry in entries:
            transfer = Transfer()
            args = entry['args']
            transfer.payload = {'id': str(args['id']), 'data': args['data']} # id will be string inside interledger
            transfers.append(transfer)
        return transfers


# Responder implementation
class EthereumResponder(Web3Initializer, Responder):
    """
    Ethereum implementation of the Responder.
    """

    def __init__(self, minter: str, contract_address: str, contract_abi: object, 
                 url: str, port: int = None, private_key: str = None, password: str = None):
        """
        :param str minter: The contract minter who is in charge of data collecting
        :param str contract_address: The address of data transfer contract implementing Interledger interface 
        :param object contract_abi: Contract ABI 
        :param str url: The web3 url
        :param int port: The web3 port, if any (default=None) 
        """
        Web3Initializer.__init__(self, url, port)
        self.contract = self.web3.eth.contract(abi=contract_abi, address=contract_address)
        self.last_block = self.web3.eth.blockNumber
        self.private_key = private_key
        self.minter = minter
        self.password = password
        self.timeout=120
        self.ledger_type = LedgerType.ETHEREUM


    async def send_data(self, nonce: str, data: bytes) -> bool:
        """Initiate the interledger receive operation to the connected ledger.

        :param string nonce: the identifier to be unique inside interledger for a data item
        :param string data: the actual content of data in bytes string

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        # Return transaction hash, need to wait for receipt
        tx_hash = None
        tx_receipt = None
        try:
            if self.private_key and not self.isUnlocked(self.minter): # needs to unlock with private key
                transaction = self.contract.functions \
                    .interledgerReceive(Web3.toInt(text=nonce), data) \
                    .buildTransaction({'from': self.minter})
                transaction.update({'nonce': self.web3.eth.getTransactionCount(self.minter)})
                signed_tx = self.web3.eth.account.signTransaction(transaction, self.private_key)
                tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            else:
                tx_hash = self.contract.functions \
                    .interledgerReceive(Web3.toInt(text=nonce), data) \
                    .transact({'from': self.minter})
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, timeout=self.timeout)

            if tx_receipt['status']:    
                logs_accept = self.contract.events.InterledgerEventAccepted().processReceipt(tx_receipt)
                logs_reject = self.contract.events.InterledgerEventRejected().processReceipt(tx_receipt)
                if len(logs_reject) != 0 and logs_reject[0]['args']['nonce'] == int(nonce):
                    return {"status": False, 
                            "error_code": ErrorCode.APPLICATION_REJECT,
                            "message": "InterledgerEventRejected() event received",
                            "tx_hash": tx_hash}
                if len(logs_accept) != 0 and logs_accept[0]['args']['nonce'] == int(nonce):
                    return {"status": True,
                            "tx_hash": tx_hash}
                else:
                    return {"status": False, 
                            "error_code": ErrorCode.TRANSACTION_FAILURE,
                            "message": "No InterledgerEventAccepted() or InterledgerEventRejected() event received",
                            "tx_hash": tx_hash}
            else:
                # TODO #tx_receipt there is not much documentation about transaction receipt
                # and the values that 'status' can get
                # if a transaction fails, I guess web3py just raises a ValueError exception
                # This return below cannot be clear, but I think it will never be executed
                return {"status": False, 
                        "error_code": ErrorCode.TRANSACTION_FAILURE,
                        "message": "Error in the transaction",
                        "tx_hash": tx_hash}
        except web3.exceptions.TimeExhausted as e :
            # Raised by web3.eth.waitForTransactionReceipt
            return {"status": False, 
                    "error_code": ErrorCode.TIMEOUT,
                    "message": "Timeout after sending the transaction",
                    "tx_hash": tx_hash,
                    "exception": e}
        except ValueError as e:
            # Raised by a contract function 
            d = eval(e.__str__())
            return {"status": False, 
                    "error_code": ErrorCode.TRANSACTION_FAILURE, 
                    "message": d['message'],
                    "tx_hash": tx_hash,
                    "exception": e}
