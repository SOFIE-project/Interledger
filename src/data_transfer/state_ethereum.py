from .state_interfaces import StateInitiator, StateResponder
from data_transfer.state_implementation import DBInitiator, DBResponder
from .ethereum import EthereumInitiator, EthereumResponder
from db_manager.db_manager import DBManager

# Extend DB Initiator & Responder
# Inject Ethereum Initiator & Responder


# StateInitiator implementation
class EthereumStateInitiator(DBInitiator):

    def __init__(self, manager: DBManager, initiator: EthereumInitiator, ledger_id:str):
        DBInitiator.__init__(self, manager, initiator, ledger_id)

# StateResponder implementation
class EthereumStateResponder(DBResponder):

    def __init__(self, manager: DBManager, responder: StateResponder, ledger_id:str):
        DBResponder.__init__(self, manager, responder, ledger_id)
