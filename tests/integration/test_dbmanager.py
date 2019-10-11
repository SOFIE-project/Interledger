from db_manager.db_manager import DBManager
from db_manager import db_manager
from unittest.mock import patch
import pytest, time

def test_manager_create_tables():

    manager = DBManager(in_memory=True)
    with patch('db_manager.db_manager.Base.metadata.create_all') as mocked_create_all:
        
        manager.create_tables()
        mocked_create_all.assert_called()


def test_manager_insert_row():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    assetId = 123
    state_left = "state_left"
    state_right = "state_right"
    owner_left = "owner_left"
    owner_right = "owner_right"
    manager.insert_row(assetId, state_left, owner_left, state_right, owner_right)

    left = manager.session.query(db_manager.LedgerLeft).first()
    right = manager.session.query(db_manager.LedgerRight).first()

    assert left.assetId == assetId
    assert left.owner == owner_left
    assert left.state == state_left

    assert right.assetId == assetId
    assert right.owner == owner_right
    assert right.state == state_right

def test_manager_delete_row():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    assetId = 123
    state_left = "state_left"
    state_right = "state_right"
    owner_left = "owner_left"
    owner_right = "owner_right"
    manager.insert_row(assetId, state_left, owner_left, state_right, owner_right)

    manager.delete_row(assetId)

    left = manager.session.query(db_manager.LedgerLeft).first()
    right = manager.session.query(db_manager.LedgerRight).first()
    assert left is None
    assert right is None


def test_manager_update_rows():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    assetIds = [123, 1234]
    states_left = ["sl1", "sl2"]
    states_right = ["sr1", "sr2"]
    owners_left = ["ol1", "ol2"]
    owners_right = ["or1", "or2"]
    manager.insert_row(assetIds[0], states_left[0], owners_left[0], states_right[0], owners_right[0])
    manager.insert_row(assetIds[1], states_left[1], owners_left[1], states_right[1], owners_right[1])

    new_states = "sl_new"
    manager.update_rows("ledger_left", assetIds, new_states)

    left = manager.session.query(db_manager.LedgerLeft).all()
    assert left[0].state == "sl_new"
    assert left[1].state == "sl_new"

def test_manager_query_by_state():

    manager = DBManager(in_memory=True)
    manager.create_tables()

    assetIds = [123, 1234, 12345]
    states_left = ["s1", "s2", "s1"]
    states_right = ["s2", "s2", "s1"]
    manager.insert_row(assetIds[0], states_left[0], "o", states_right[0], "o")
    manager.insert_row(assetIds[1], states_left[1], "o", states_right[1], "o")
    manager.insert_row(assetIds[2], states_left[2], "o", states_right[2], "o")

    ids = manager.query_by_state("ledger_left", "s1")

    assert ids[0].assetId == 123
    assert ids[1].assetId == 12345

    ids = manager.query_by_state("ledger_right", "s2")

    assert ids[0].assetId == 123
    assert ids[1].assetId == 1234
