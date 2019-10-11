from db_manager.db_manager import DBManager
from db_manager import db_manager
from sofie_asset_transfer.interfaces import Responder
from sofie_asset_transfer.state_implementation import DBResponder
import pytest

def test_state_responder_constructor():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    responder = DBResponder(manager, Responder(), "ledger_right")
    assert responder.manager == manager
    assert responder.ledgerId == "ledger_right"
