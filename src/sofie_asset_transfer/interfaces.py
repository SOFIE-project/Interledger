from typing import List, Dict

class Transfer(object):
    pass


class Initiator(object):
    """
    An Initiator is in charge to catch events coming from the ledger it listens to, and commit or abort the transfers into the same ledger. 
    """

    async def get_transfers(self) -> List[Transfer]:
        """Listen for events and, for each caught event, transfer the its information. 

        :returns: The event transfer lists
        :rtype: list
        """
        assert False, "must be implemented in child class"

    async def abort_transfer(self, transfer: Transfer) -> bool:
        """Initiate the abort operation to the connected ledger.

        :param object transfer: the transfer to abort

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"

    async def commit_transfer(self, transfer: Transfer) -> bool:
        """Initiate the commit operation to the connected ledger.

        :param object transfer: the transfer to commit

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # return True/False for success/failure
        assert False, "must be implemented in child class"



class Responder(object):
    """
    Start the asset transfer protocol after receiving the transfer's information.
    """

    async def receive_transfer(self, transfer: Transfer) -> bool:
        """Initiate the accept operation to the connected ledger.

        :param object transfer: the transfer to forward

        :returns: True if the operation goes well; False otherwise
        :rtype: bool
        """
        # actually can be error / reject / accept, tristate ?
        # but for now: True = accept, False = reject
        assert False, "must be implemented in child class"