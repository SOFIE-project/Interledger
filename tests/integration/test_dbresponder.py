from db_manager.db_manager import DBManager
from db_manager import db_manager
from sofie_asset_transfer.interfaces import Responder, Transfer
from sofie_asset_transfer.state_implementation import DBResponder
from unittest.mock import patch
import pytest, time

#####  PROTOCOL METHODS  #####

# accept

# patch db methods

def test_responder_store_accept():

    manager = DBManager(in_memory=True)
    manager.create_tables()
    
    responder = DBResponder(manager, Responder(), "ledger_right")
    assetId = 123
    
    manager.insert_row(assetId, "s1", "test_owner", "s2", "test_owner")

    with patch('db_manager.db_manager.DBManager.update_rows') as mocked_update:

        responder.store_accept(assetId)
        mocked_update.assert_called_with(responder.ledgerId, [assetId], "Here")
    

#####  MODULE METHODS  #####

# receive_transfer

# patch super class not implemented methods
# patch db_manager methods

@pytest.mark.asyncio
async def test_state_responder_receive_transfer():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    responder = DBResponder(manager, Responder(), "ledger_right")
    transfer = Transfer()
    transfer.data = {}
    transfer.data["assetId"] = 123
    with patch("sofie_asset_transfer.interfaces.Responder.receive_transfer", return_value=True) as mock_receive_transfer:
        with patch("sofie_asset_transfer.state_implementation.DBResponder.store_accept") as mocked_state_accept:

            await responder.receive_transfer(transfer)
            mocked_state_accept.assert_called_with(123)
