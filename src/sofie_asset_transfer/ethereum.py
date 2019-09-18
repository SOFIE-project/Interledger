from .interfaces import Initiator, Responder
from .interledger import Transfer
import time, asyncio
from typing import List
from web3 import Web3

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

    # Helper function
    def create_transfer_list(self, entries):
        """Helper function to create a list of Transfer object from a list of web3 event entries
        """

        transfers = []
        for e in entries:
            args = e['args']
            t = Transfer()
            t.data = {'tokenId': args['id'],
                      'assetId': args['data'],
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
        :rtype: bool
        """

        # Return transaction hash, need to wait for receipt
        tx_hash = self.contract_init.functions.abort(transfer.data["tokenId"]).transact({'from': self.minter})
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        if tx_receipt['status']:
            return True
        else:
            return False


    async def commit_transfer(self, transfer: Transfer) -> bool:
        """Initiate the commit operation to the connected ledger.

        :param object transfer: the transfer to commit

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        
        # Return transaction hash, need to wait for receipt
        tx_hash = self.contract_init.functions.commit(transfer.data["tokenId"]).transact({'from': self.minter})
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        if tx_receipt['status']:
            return True
        else:
            return False


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


    async def receive_transfer(self, transfer: Transfer) -> bool:
        """Initiate the accept operation to the connected ledger.

        :param object transfer: the transfer to forward

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """

        # Return transaction hash, need to wait for receipt
        tx_hash = self.contract_resp.functions.accept(transfer.data["tokenId"]).transact({'from': self.minter})
        tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        if tx_receipt['status']:
            return True
        else:
            return False
