from .interfaces import Initiator, Responder, Transfer
from db_manager.db_manager import DBManager
from typing import List
from enum import Enum

class AssetState(Enum):
    """State of an asset of the protocol
    """
    HERE = 1
    TRANSFER_OUT = 2
    NOT_HERE = 3

class StateInitiator(Initiator):
    """Child class of Initiator.
    This interface exposes to the Initiator the methods needed to store the states of the assets in a persistent way
    """

    # Store state

    def store_transfer_out(self, assetId_list: List[int]):
        """Store the state of the input asset ids to Transfer Out
        :param list assetId_list: The list of asset ids
        """
        assert False, "must be implemented in child class"

    def store_commit(self, assetId: int):
        """Store the state of the input asset ids to Not Here
        :param list assetId: The asset id
        """
        assert False, "must be implemented in child class"

    def store_abort(self, assetId: int):
        """Store the state of the input asset ids to Here
        :param list assetId: The asset id
        """
        assert False, "must be implemented in child class"

    # Query methods

    def query_by_state(self, state: str) -> List[int]:
        """Query the asset ids matching the input state
        :param string state: The input state
        """
        assert False, "must be implemented in child class"


class StateResponder(Responder):
    """Child class of Responder.
    This interface exposes to the Responder the methods needed to store the states of the assets in a persistent way
    """

    # Store state

    def store_accept(self, assetId: int):
        """Store the state of the input asset ids to Here
        :param list assetId: The asset id
        """
        assert False, "must be implemented in child class"


    # Query methods

    def query_by_state(self, state: str) -> List[int]:
        """Query the asset ids matching the input state
        :param string state: The input state
        """
        assert False, "must be implemented in child class"
