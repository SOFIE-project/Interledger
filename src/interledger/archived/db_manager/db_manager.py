from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import tuple_

Base = declarative_base()

class LedgerLeft(Base):
    """Table tracking the assets in a ledger
    """
    __tablename__ = "ledger_left"

    assetId = Column(Integer, primary_key=True)
    state = Column(String(250), nullable=False)
    owner = Column(String(250), nullable=False)

class LedgerRight(Base):
    """Table tracking the assets in a ledger
    """
    __tablename__ = "ledger_right"

    assetId = Column(Integer, primary_key=True)
    state = Column(String(250), nullable=False)
    owner = Column(String(250), nullable=False)
    

class DBManager():
    """Class to insert / update / remove and query DB records describing the IL assets
    """

    def __init__(self, url="default", in_memory=False):
        """
        :param string url: The url of the database
        :param bool in_memory: In memory database if True, persistent otherwise (default)
        """
        if not in_memory:
            self.engine = create_engine(f"sqlite:///{url}.db")
        else:
            self.engine = create_engine("sqlite://")

        Base.metadata.bind = self.engine
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()

    def create_tables(self):
        """Create the tables in the db
        """
        Base.metadata.create_all(self.engine)


    def update_rows(self, ledgerId, assetId_list, new_state):
        """Update rows identified by the assetId with a new state
        :param string ledgerId: The name of the table to update
        :param list assetId_list: The list of the assets to update
        :param string new_state: The new state of the assets
        """

        rows = None
        if ledgerId == 'ledger_left':
            query = self.session.query(LedgerLeft)
            rows = query.filter(LedgerLeft.assetId.in_(assetId_list)).all()
        elif ledgerId == 'ledger_right':
            query = self.session.query(LedgerRight)
            rows = query.filter(LedgerRight.assetId.in_(assetId_list)).all()
        else:
            raise ValueError(f"db_manager: ERROR: table {ledgerId} not present")

        for idx, r in enumerate(rows):
            r.state = new_state

        self.session.commit()

    def insert_row(self, assetId, state_left, owner_left, state_right, owner_right):
        """Insert a new record. A new record should be inserted in both the tables
        :param int assetId: The id of the new asset record
        :param string state_left: The state in the left ledger
        :param string owner_left: The asset owner's id in the left ledger 
        :param string state_right: The state in the right ledger
        :param string owner_right: The asset owner's id in the right ledger 
        """
        new_left = LedgerLeft(assetId=assetId, state=state_left, owner=owner_left)
        new_right = LedgerRight(assetId=assetId, state=state_right, owner=owner_right)
        # new_asset = Asset(id=assetId, left=new_left, right=new_right)
        self.session.add(new_left)
        self.session.add(new_right)
        # self.session.add(new_asset)
        self.session.commit()
        
    def delete_row(self, assetId):
        """Remove the records connected to the input id
        :param int assetId: The id of the asset
        """
        sl = self.session.query(LedgerLeft).get(assetId)
        sr = self.session.query(LedgerRight).get(assetId)
        # asset = self.session.query(Asset).get(assetId)

        self.session.delete(sl)
        self.session.delete(sr)
        # self.session.delete(asset)

    def query_by_state(self, ledgerId, state):
        """Query all the asset ids which match the input state
        :param string ledgerId: The ledger to query
        :param string state: The input state
        """        
        rows = None
        if ledgerId == 'ledger_left':
            query = self.session.query(LedgerLeft)
            rows = query.filter(LedgerLeft.state == state).all()
        elif ledgerId == 'ledger_right':
            query = self.session.query(LedgerRight)
            rows = query.filter(LedgerRight.state == state).all()
        else:
            raise ValueError(f"db_manager: ERROR: table {ledgerId} not present")

        return rows
