from db_manager.db_manager import DBManager
from db_manager import db_manager
from sofie_asset_transfer.interfaces import Initiator, Transfer
from sofie_asset_transfer.state_implementation import DBInitiator
from unittest.mock import patch
import pytest, time

#####  PROTOCOL METHODS  #####

# transfer_out, commit, abort

# patch db methods

def help_setup_initiator_and_insert_row(assetId):

    manager = DBManager(in_memory=True)
    manager.create_tables()

    initiator = DBInitiator(manager, Initiator(), "ledger_left")
    manager.insert_row(assetId, "s1", "test_owner", "s2", "test_owner")

    return initiator


def test_initiator_store_transfer_out():

    assetId = 123
    initiator = help_setup_initiator_and_insert_row(assetId)

    with patch('db_manager.db_manager.DBManager.update_rows') as mocked_update:
        
        initiator.store_transfer_out([assetId])
        mocked_update.assert_called_with(initiator.ledgerId, [assetId], "Transfer Out")

def test_initiator_store_commit():

    assetId = 123
    initiator = help_setup_initiator_and_insert_row(assetId)

    with patch('db_manager.db_manager.DBManager.update_rows') as mocked_update:

        initiator.store_commit(assetId)
        mocked_update.assert_called_with(initiator.ledgerId, [assetId], "Not Here")

def test_initiator_store_abort():

    assetId = 123
    initiator = help_setup_initiator_and_insert_row(assetId)

    with patch('db_manager.db_manager.DBManager.update_rows') as mocked_update:

        initiator.store_abort(assetId)
        mocked_update.assert_called_with(initiator.ledgerId, [assetId], "Here")
    

#####  MODULE METHODS  #####

# get_transfers, commit_transfer, abort_transfer
# receive_transfer

# patch super class not implemented methods
# patch db_manager methods

@pytest.mark.asyncio
async def test_state_initiator_get_transfers():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    initiator = DBInitiator(manager, Initiator(), "ledger_left")
    transfer = Transfer()
    transfer.data = {}
    transfer.data["assetId"] = 123
    with patch("sofie_asset_transfer.interfaces.Initiator.get_transfers", return_value=[transfer]) as mock_get_transfers:
        with patch("db_manager.db_manager.DBManager.update_rows") as mocked_update:

            await initiator.get_transfers()
            mocked_update.assert_called_with(initiator.ledgerId, [123], "Transfer Out")

@pytest.mark.asyncio
async def test_state_initiator_commit_transfer():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    initiator = DBInitiator(manager, Initiator(), "ledger_left")
    transfer = Transfer()
    transfer.data = {}
    transfer.data["assetId"] = 123
    with patch("sofie_asset_transfer.interfaces.Initiator.commit_transfer", return_value=True) as mock_commit_transfer:
        with patch("sofie_asset_transfer.state_implementation.DBInitiator.store_commit") as mocked_state_commit:

            await initiator.commit_transfer(transfer)
            mocked_state_commit.assert_called_with(123)

@pytest.mark.asyncio
async def test_state_initiator_abort_transfer():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    initiator = DBInitiator(manager, Initiator(), "ledger_left")
    transfer = Transfer()
    transfer.data = {}
    transfer.data["assetId"] = 123
    with patch("sofie_asset_transfer.interfaces.Initiator.abort_transfer", return_value=True) as mock_abort_transfer:
        with patch("sofie_asset_transfer.state_implementation.DBInitiator.store_abort") as mocked_state_abort:

            await initiator.abort_transfer(transfer)
            mocked_state_abort.assert_called_with(123)