from sofie_asset_transfer.interfaces import Initiator, Responder
from sofie_asset_transfer.interledger import Interledger


def test_interledger_init():
    # Test initialization of interledger

    init = Initiator()
    resp = Responder()

    interledger = Interledger(init, resp)

    assert interledger.initiator == init
    assert interledger.responder == resp
    assert len(interledger.transfers) == 0
    assert len(interledger.transfers_sent) == 0
    assert interledger.pending == 0
    assert interledger.keep_running == True    


def test_interledger_stop():
    
    interledger = Interledger(None, None)

    interledger.stop()

    assert interledger.keep_running == False