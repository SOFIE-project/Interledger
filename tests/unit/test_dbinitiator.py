from db_manager.db_manager import DBManager
from db_manager import db_manager
from sofie_asset_transfer.interfaces import Initiator
from sofie_asset_transfer.state_implementation import DBInitiator
import pytest

def test_state_initiator_constructor():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    initiator = DBInitiator(manager, Initiator(), "ledger_left")
    assert initiator.manager == manager
    assert initiator.ledgerId == "ledger_left"