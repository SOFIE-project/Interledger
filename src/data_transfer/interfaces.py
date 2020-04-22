from enum import Enum


# Error codes
class ErrorCode(Enum):
    TIMEOUT = 1
    TRANSACTION_FAILURE = 2
    UNSUPPORTED_KSI_HASH = 3
    APPLICATION_REJECT = 4
    
    
# Ledger types
class LedgerType(Enum):
    ETHEREUM = 1
    HYPERLEDGER_FABRIC = 2
    HYPERLEDGER_INDY = 3
    KSI = 4


class Initiator(object):
    """
    An Initiator is in charge to catch events coming from the ledger it listens to, and commit or abort the data sending into the same originating ledger. 
    """

    async def listen_for_events(self) -> list:
        """Listen for events and, for each caught event, transfer the its payload information. 

        :returns: The event transfer lists
        :rtype: list
        """
        assert False, "must be implemented in child class"

    async def commit_sending(self, id: str, data: bytes = None) -> bool:
        """Initiate the commit operation to the connected ledger.

        :param string id: the identifier in the originating ledger for a data item
        :param bytes data: optional, used for passing data from Responder to Initiator

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"

    async def abort_sending(self, id: str, reason: int) -> bool:
        """Initiate the abort operation to the connected ledger.

        :param string id: the identifier in the originating ledger for a data item
        :param string reason: the description on why the data transfer is aborted

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"


class Responder(object):
    """
    Start the data transfer protocol after receiving the transfer's payload information.
    """

    async def send_data(self, nonce: str, data: bytes) -> bool:
        """Initiate the interledger receive operation to the connected ledger.

        :param string nonce: the identifier to be unique inside interledger for a data item
        :param bytes data: the actual content of data

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # actually can be error / reject / accept, tristate ?
        # but for now: True = accept, False = reject
        assert False, "must be implemented in child class"
