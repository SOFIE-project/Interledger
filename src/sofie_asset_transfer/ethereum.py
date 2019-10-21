from .interfaces import Initiator, Responder, ErrorCode
from .interledger import Transfer
from typing import List
from web3 import Web3
import time, asyncio, web3

# Web3 util
class Web3Initializer:

    def __init__(self, url: str, port=None):
        
        path = url
        if port is not None:
            path = path + ':' + str(port)
        self.web3 = Web3(Web3.HTTPProvider(path))


# Initiator implementation

class EthereumInitiator(Web3Initializer, Initiator):
    """
    Ethereum implementation of the Initiator.
    """

    def __init__(self, minter: str, contract: object, url: str, port=None):
        """
        :param str minter: The contract minter / creator
        :param object contract: The asset transfer contract 
        :param str url: The web3 url
        :param int port: The web3 port, if any (default=None) 
        """
        Web3Initializer.__init__(self, url, port)
        self.contract_init = contract
        self.last_block = self.web3.eth.blockNumber
        self.minter = minter
        self.timeout = 120

    # Helper function
    def create_transfer_list(self, entries):
        """Helper function to create a list of Transfer object from a list of web3 event entries
        """

        transfers = []
        for e in entries:
            args = e['args']
            t = Transfer()
            t.data = {'assetId': args['id'],
                      'data': args['data'],
                      'from': args['from']}
            transfers.append(t)
        return transfers

    # Initiator functions

    async def get_transfers(self) -> List[Transfer]:
        """Listen for events fired by the Initiator injected contract stored in the connected Ethereum network.

        :returns: The event transfer lists
        :rtype: list
        """

        # Needs to be blocking
        while True :

            # Create event filter for 'TransferOut' event: the event to pay attention to
            filt = self.contract_init.events.TransferOut().createFilter(fromBlock=self.last_block+1) # +1 otherwise gets again older block
            entries = filt.get_all_entries()
            self.last_block = self.web3.eth.blockNumber

            if len(entries) == 0:

                await asyncio.sleep(1)
                entries = filt.get_all_entries()
                self.last_block = self.web3.eth.blockNumber

            # Transform entries in Transfer object
            return self.create_transfer_list(entries)


    async def abort_transfer(self, transfer: Transfer) -> bool:
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
            tx_hash = self.contract_init.functions.abort(transfer.data["assetId"]).transact({'from': self.minter})
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


    async def commit_transfer(self, transfer: Transfer) -> bool:
        """Initiate the commit operation to the connected ledger.

        :param object transfer: the transfer to commit

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
            tx_hash = self.contract_init.functions.commit(transfer.data["assetId"]).transact({'from': self.minter})
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


# Responder implementation

class EthereumResponder(Web3Initializer, Responder):
    """
    Ethereum implementation of the Responder.
    """

    def __init__(self, minter: str, contract: object, url: str, port=None):
        """
        :param str minter: The contract minter / creator
        :param object contract: The asset transfer contract 
        :param str url: The web3 url
        :param int port: The web3 port, if any (default=None) 
        """

        Web3Initializer.__init__(self, url, port)
        self.contract_resp = contract
        self.minter = minter
        self.timeout=120


    async def receive_transfer(self, transfer: Transfer) -> bool:
        """Initiate the accept operation to the connected ledger.

        :param object transfer: the transfer to forward

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
        try:
            tx_hash = self.contract_resp.functions.accept(transfer.data["assetId"]).transact({'from': self.minter})
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, timeout=self.timeout) # Deafault 120 seconds

            if tx_receipt['status']:            
                return {"status": True,
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