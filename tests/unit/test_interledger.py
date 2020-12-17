
from interledger.adapter.interfaces import Initiator, Responder
from interledger.interledger import Interledger
from interledger.transfer import TransferStatus, Transfer


#import sys, os
#sys.path.append(os.path.realpath('./src'))
def test_interledger_init():
    # Test initialization of interledger

    init = Initiator()
    resp = Responder()

    interledger = Interledger(init, resp)

    assert interledger.initiator == init
    assert interledger.responder == resp
    assert len(interledger.transfers) == 0
    assert len(interledger.transfers_sent) == 0
    assert len(interledger.results_committing) == 0
    assert len(interledger.results_commit) == 0
    assert len(interledger.results_aborting) == 0
    assert len(interledger.results_abort) == 0
    assert interledger.up == False 


def test_interledger_stop():
    
    interledger = Interledger(None, None)
    interledger.stop()

    assert interledger.up == False


def return_transfer_list():

    t1 = Transfer()
    t2 = Transfer()
    t3 = Transfer()
    t4 = Transfer()
    t5 = Transfer()

    # t1 is State.ready by default
    t2.status = TransferStatus.SENT
    t3.status = TransferStatus.RESPONDED
    t4.status = TransferStatus.CONFIRMING
    t5.status = TransferStatus.FINALIZED

    return [t1, t2, t3, t4, t5]



def test_interledger_cleanup():

    interledger = Interledger(None, None)
    ts1 = return_transfer_list()

    interledger.transfers.extend(ts1)
    interledger.transfers_sent.extend(ts1)

    interledger.cleanup()

    assert len(interledger.transfers) is 4
    assert len(interledger.transfers_sent) is 5