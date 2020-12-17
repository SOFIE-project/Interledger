from enum import Enum

from ..transfer import TransferStatus, Transfer


# Error codes
class ErrorCode(Enum):
    TIMEOUT = 1
    TRANSACTION_FAILURE = 2
    UNSUPPORTED_KSI_HASH = 3
    APPLICATION_REJECT = 4
    INQUIRY_REJECT = 5


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

    async def commit_sending(self, id: str, data: bytes = None) -> dict:
        """Initiate the commit operation to the connected ledger.

        :param string id: the identifier in the originating ledger for a data item
        :param bytes data: optional, used for passing data from Responder to Initiator

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'commit_status': bool,
            'commit_tx_hash': str,
            'exception': object,# only with errors
            'commit_error_code': Enum, # only with errors
            'commit_message': str      # only with errors
        }
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"

    async def abort_sending(self, id: str, reason: int) -> dict:
        """Initiate the abort operation to the connected ledger.

        :param string id: the identifier in the originating ledger for a data item
        :param int reason: the description on why the data transfer is aborted

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'abort_status': bool,
            'abort_tx_hash': str,
            'exception': object,# only with errors
            'abort_error_code': Enum, # only with errors
            'abort_message': str      # only with errors
        }
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"


class Responder(object):
    """
    Start the data transfer protocol after receiving the transfer's payload information.
    """

    async def send_data(self, nonce: str, data: bytes) -> dict:
        """Initiate the interledger receive operation to the connected ledger.

        :param string nonce: the identifier to be unique inside interledger for a data item
        :param bytes data: the actual content of data

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        # actually can be error / reject / accept, tristate ?
        # but for now: True = accept, False = reject
        assert False, "must be implemented in child class"


class MultiResponder(Responder):
    """
    Similar working unit as Responder, but should be used under multi-ledger mode only.
    """

    async def send_data_inquire(self, nonce: str, data: bytes) -> dict:
        """Invoke the inquiry operation to the connected ledger
        :param string nonce: the identifier to be unique inside interledger for a data item
        :param bytes data: the actual content of data

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        assert False, "must be implemented in child class"

    async def abort_send_data(self, nonce: str, reason: int) -> dict:
        """Invoke the abort sending operation to the connected ledger
        :param string nonce: the identifier to be unique inside interledger for a data item
        :param int reason: the description on why the data transfer is aborted

        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        """
        assert False, "must be implemented in child class"


class ILStateManager:
    """
    Interledger state manager is the adapter that interacts with 
    state layers of different types for the creation and update of 
    transfer entries that are accessed by participating parties
    """

    def __init__(self) -> None:
        assert False, "must be implemented in child class"

    async def create_entry(self, id: str, transfer: Transfer) -> bool:
        """Create entry of transfer in the state layer
        :param string id: the id used for accessing the state layer 
        :param Transfer transfer: the transfer object to be passed

        :returns: True if the entry is created successfully; False otherwise
        """
        assert False, "must be implemented in child class"

    async def signal_send_acceptance(self, id: str) -> bool:
        """Update the state layer a transfer corresponding to a given id
        will be carried out by this IL node
        :param string id: the id used for accessing the state layer

        :returns: True if the signal of accepted; False otherwise
        """
        assert False, "must be implemented in child class"

    async def update_entry(self, id: str, status: TransferStatus, transfer: Transfer = None) -> bool:
        """Update the transfer entry status, and optionally its content in state layer
        :param string id: the id used for accessing the state layer
        :param TransferStatus status: the transfer status to be updated to
        :param Transfer transfer (optional): the transfer object that carries the actual content, 
        if present it is used to update the transfer payload in the state layer

        :returns: True if the update works correctly; False otherwise
        """
        assert False, "must be implemented in child class"

    async def receive_entry_events(self, event: TransferStatus) -> None:
        """Check emmited events from state layer about transfers that become ready
        or responded, add these to the correspoinding fields
        :param EntryEvent: the event type based upon to receive the entries
        """
        assert False, "must be implemented in child class"
