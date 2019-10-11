from db_manager.db_manager import DBManager
import pytest

def test_manager_creation():

    manager = DBManager(in_memory=True)
    assert manager.session is not None
    assert manager.engine is not None