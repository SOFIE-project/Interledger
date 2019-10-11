from .state_interfaces import StateInitiator, StateResponder, AssetState
from .interfaces import Initiator, Responder, Transfer
from db_manager.db_manager import DBManager
from typing import List

class DBInitiator(StateInitiator):
    """Child class of StateInitiator.
    This sub-class has a DB manager to query - store the state of the assets in a persisten way.
    This class does not implement the Initiator methods. An Initiator implementation should be injected
    """

    def __init__(self, manager: DBManager, initiator: Initiator, ledgerId: str):
        """Constructor
        :param DBManager manager: The DBManager object
        :param Initiator initiator: The Initiator object
        :param string ledgerId: The id of the ledger connected to. It should match the name of the ledger DB table
        """
        super().__init__()
        self.manager = manager
        self.ledgerId = ledgerId
        self.initiator = initiator
        self.stateMap = {
            AssetState.HERE: "Here",
            AssetState.TRANSFER_OUT: "Transfer Out",
            AssetState.NOT_HERE: "Not Here"
        }

    # Store state

    def store_transfer_out(self, assetId_list):
        """Store the state of the input asset ids to Transfer Out
        :param list assetId_list: The list of asset ids
        """
        self.manager.update_rows(self.ledgerId, assetId_list, self.stateMap[AssetState.TRANSFER_OUT])

    def store_commit(self, assetId):
        """Store the state of the input asset ids to Not Here
        :param list assetId: The asset id
        """
        self.manager.update_rows(self.ledgerId, [assetId], self.stateMap[AssetState.NOT_HERE])

    def store_abort(self, assetId):
        """Store the state of the input asset ids to Here
        :param list assetId: The asset id
        """
        self.manager.update_rows(self.ledgerId, [assetId], self.stateMap[AssetState.HERE])


    # Query methods

    def query_by_state(self, state):
        """Query the asset ids matching the input state
        :param string state: The input state
        """
        return self.manager.query_by_state(self.ledgerId, state)


    # Parent methods extension

    async def get_transfers(self) -> List[Transfer]:
        """Extension of the parent method. Updates the DB.
        :returns: The list of new transfers
        :rtype: list
        """

        transfers = self.initiator.get_transfers()
        id_list = [t.data["assetId"] for t in transfers]
        self.store_transfer_out(id_list)

        return transfers

    async def abort_transfer(self, transfer: Transfer) -> bool:
        """Extension of the parent method. Updates the DB.

        :param object transfer: the transfer to abort

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        
        if self.initiator.abort_transfer(transfer):
            self.store_abort(transfer.data['assetId'])

    async def commit_transfer(self, transfer: Transfer) -> bool:
        """Extension of the parent method. Updates the DB.

        :param object transfer: the transfer to commit

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        
        if self.initiator.commit_transfer(transfer):
            self.store_commit(transfer.data['assetId'])


class DBResponder(StateResponder):
    """Child class of StateResponder.
    This sub-class has a DB manager to query - store the state of the assets in a persisten way
    This class does not implement the Responder methods. A responder implementation should be injected
    """

    def __init__(self, manager: DBManager, responder: Responder, ledgerId: str):
        """Constructor
        :param DBManager manager: The DBManager object
        :param Responder responder: The Responder object
        :param string ledgerId: The id of the ledger connected to. It should match the name of the ledger DB table
        """
        super().__init__()
        self.manager = manager
        self.ledgerId = ledgerId
        self.responder = responder
        self.stateMap = {
            AssetState.HERE: "Here",
            AssetState.TRANSFER_OUT: "Transfer Out",
            AssetState.NOT_HERE: "Not Here"
        }

    # Store state

    def store_accept(self, assetId):
        """Store the state of the input asset ids to Here
        :param list assetId: The asset id
        """
        self.manager.update_rows(self.ledgerId, [assetId], self.stateMap[AssetState.HERE])


    # Query methods

    def query_by_state(self, state):
        """Query the asset ids matching the input state
        :param string state: The input state
        """
        return self.manager.query_by_state(self.ledgerId, state)


    # Parent methods extension

    async def receive_transfer(self, transfer: Transfer) -> bool:
        """Extension of the parent method. Updates the DB.

        :param object transfer: the transfer to accept

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        
        if self.responder.receive_transfer(transfer):
            self.store_accept(transfer.data['assetId'])

