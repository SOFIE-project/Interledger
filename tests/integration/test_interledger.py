from data_transfer.interledger import Interledger, Transfer, State
from data_transfer.interfaces import LedgerType
from typing import List
import pytest, time
import asyncio 
from unittest.mock import patch
from uuid import uuid4

# # # Global view
# #
# #  Ledger <- Initiator <- Interledeger -> Responder -> Ledger
#

# # # Local view
# #
# #  MockInitiator <- Interledeger -> MockResponder
#

class MockInitiator:

    def __init__(self, events: List):
        self.events = events
        self.ledger_type = LedgerType.ETHEREUM

    async def listen_for_events(self):
        result = []
        if len(self.events) > 0:
            result = self.events.copy()
            self.events.clear()
        return result
    
    async def commit_sending(self, id: str):
        return {"commit_status": True, "commit_tx_hash" : '0x111'}

    async def abort_sending(self, id: str, reason: int):
         return {"abort_status": True, "abort_tx_hash" : '0x222'}


# Responder which getting positive result

class MockResponder:

    def __init__(self):
        self.events = []
        self.ledger_type = LedgerType.ETHEREUM

    async def send_data(self, nonce: str, data: bytes):

        return {"status": 42}


# Responder which getting negative result

class MockResponderAbort:

    async def send_data(self, nonce: str, data: bytes):

        return {"status": False}



#
# Test receive_transfer
#

@pytest.mark.asyncio
async def test_interledger_receive_transfer():

    t = Transfer()
    t.payload = {}
    init = MockInitiator([t])
    resp = MockResponder()
    interledger = Interledger(init, resp)
    # interledger.test_interrupt = True

    task = asyncio.ensure_future(interledger.receive_transfer())    
    assert task.done() == False
    l = await task

    assert init.events == []
    assert len(interledger.transfers) == 1
    assert l == 1
    assert interledger.transfers[0].state == State.READY

##############################


#
# Test send_transfer
#
@pytest.mark.asyncio
async def test_interledger_send_transfer():

    t = Transfer()
    t.payload = {}
    t.payload['nonce'] = str(uuid4().int)
    t.payload['data'] =  b"dummy"
    i = Interledger(MockInitiator([]), MockResponder())

    i.transfers = [t]

    task = asyncio.ensure_future(i.send_transfer())
    assert task.done() == False
    await task

    assert len(i.transfers_sent) == 1
 
    tr = i.transfers[0]
    assert tr.state == State.SENT
    assert asyncio.isfuture(tr.send_task)

    await tr.send_task
    assert tr.send_task.done() == True

#
# Test transfer_result
#
@pytest.mark.asyncio
async def test_interledger_transfer_result():

    async def foo():
        return 42

    i = Interledger(MockInitiator([]), MockResponder())
    
    t = Transfer()
    t.state = State.SENT
    t.send_task = asyncio.ensure_future(foo())
    i.transfers_sent = [t]
    
    task = asyncio.ensure_future(i.transfer_result())
    assert task.done() == False
    await task

    assert len(i.transfers_sent) == 0
    assert len(i.transfers_responded) == 1
    tr = i.transfers_responded[0]
    assert tr.state == State.RESPONDED
    assert tr.result == 42


#
# Test transfer_result with a commit
#  - need ad-hoc commit future
#
@pytest.mark.asyncio
async def test_interledger_process_result_commit():

    i = Interledger(MockInitiator([]), MockResponder())
    
    t = Transfer()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.state = State.RESPONDED
    t.result = {"status": True}
    i.transfers_responded = [t]

    task = asyncio.ensure_future(i.process_result())
    assert task.done() == False
    await task

    tr = i.results_committing[0]
    assert tr.state == State.CONFIRMING
    assert tr.result['status'] == True
    assert len(i.results_commit) == 0
    assert len(i.results_abort) == 0
    
    assert len(i.transfers_responded) == 0

#
# Test transfer_result with an abort
#
@pytest.mark.asyncio
async def test_interledger_process_result_abort():

    i = Interledger(MockInitiator([]), MockResponder())
    
    t = Transfer()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.state = State.RESPONDED
    t.result = {"status": False}
    i.transfers_responded = [t]
    
    task = asyncio.ensure_future(i.process_result())
    assert task.done() == False
    await task

    tr = i.results_aborting[0]
    assert tr.state == State.CONFIRMING
    assert tr.result['status'] == False
    assert len(i.results_commit) == 0
    assert len(i.results_abort) == 0

    assert len(i.transfers_responded) == 0


#
# Test confirm_transfer with a commit
#
@pytest.mark.asyncio
async def test_interledger_confirm_transfer_commit():
    async def foo():
        return {'commit_status': True,
                'commit_tx_hash': '0x333'}

    i = Interledger(MockInitiator([]), MockResponder())

    t = Transfer()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.result = {}
    t.state = State.CONFIRMING
    t.confirm_task = asyncio.ensure_future(foo())
    i.results_committing = [t]
    
    task = asyncio.ensure_future(i.confirm_transfer())
    assert task.done() == False
    await task

    res = i.results_commit[0]
    assert t.state == State.FINALIZED
    assert res['commit_status'] == True
    assert res['commit_tx_hash'] == '0x333'
    assert len(i.results_commit) == 1
    assert len(i.results_abort) == 0

    assert len(i.results_committing) == 0


#
# Test confirm_transfer with an abort
#
@pytest.mark.asyncio
async def test_interledger_confirm_transfer_abort():
    async def foo():
        return {'abort_status': True,
                'abort_tx_hash': '0x444'}

    i = Interledger(MockInitiator([]), MockResponder())

    t = Transfer()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.result = {}
    t.state = State.CONFIRMING
    t.confirm_task = asyncio.ensure_future(foo())
    i.results_aborting = [t]
    
    task = asyncio.ensure_future(i.confirm_transfer())
    assert task.done() == False
    await task

    res = i.results_abort[0]
    assert t.state == State.FINALIZED
    assert res['abort_status'] == True
    assert res['abort_tx_hash'] == '0x444'
    assert len(i.results_abort) == 1
    assert len(i.results_commit) == 0

    assert len(i.results_aborting) == 0

# ##############################

# #
# # Test run
# # - with no cleanup
# # - with cleanup
# #
    
@pytest.mark.asyncio
async def test_interledger_run_no_cleanup():

    l1, l2, l3 = [], [], []
    for i in range(4):
        t1, t2, t3 = Transfer(), Transfer(), Transfer()
        t1.payload, t2.payload, t3.payload = {}, {}, {}
        t1.payload['nonce'], t1.payload['id'], t1.payload['data'] = str(uuid4().int), '1', b"dummy1"
        t2.payload['nonce'], t2.payload['id'], t2.payload['data'] = str(uuid4().int), '2', b"dummy2"
        t3.payload['nonce'], t3.payload['id'], t3.payload['data'] = str(uuid4().int), '3', b"dummy3"
        l1.append(t1)
        l2.append(t2)
        l3.append(t3)

    init = MockInitiator(l1)
    i = Interledger(init, MockResponder())

    with patch("data_transfer.interledger.Interledger.cleanup") as mock_cleanup:

        task = asyncio.ensure_future(i.run())

        time = 0.5
        # Consume l1
        await asyncio.sleep(time)   # Simulate interledger running

        # New events
        init.events = l2
        # Consume l2
        await asyncio.sleep(time)   # Simulate interledger running

        # New events
        i.responder = MockResponderAbort()
        init.events = l3
        # Consume l3, but with a responder returning False -> abort
        await asyncio.sleep(time)   # Simulate interledger running

        assert len(i.transfers) == 12
        assert len(i.transfers_sent) == 0
        assert len(i.transfers_responded) == 0
        assert len(i.results_committing) == 0
        assert len(i.results_aborting) == 0
        assert len(i.results_commit) == 8
        assert len(i.results_abort) == 4

        i.stop()
        await task

@pytest.mark.asyncio
async def test_interledger_run_with_cleanup():

    l1, l2, l3 = [], [], []
    for i in range(4):
        t1, t2, t3 = Transfer(), Transfer(), Transfer()
        t1.payload, t2.payload, t3.payload = {}, {}, {}
        t1.payload['nonce'], t1.payload['id'], t1.payload['data'] = str(uuid4().int), '1', b"dummy1"
        t2.payload['nonce'], t2.payload['id'], t2.payload['data'] = str(uuid4().int), '2', b"dummy2"
        t3.payload['nonce'], t3.payload['id'], t3.payload['data'] = str(uuid4().int), '3', b"dummy3"
        l1.append(t1)
        l2.append(t2)
        l3.append(t3)

    init = MockInitiator(l1)
    i = Interledger(init, MockResponder())

    task = asyncio.ensure_future(i.run())

    time = 0.5
    # Consume l1
    await asyncio.sleep(time)   # Simulate interledger running

    # New events
    init.events = l2
    # Consume l2
    await asyncio.sleep(time)   # Simulate interledger running

    # New events
    i.responder = MockResponderAbort()
    init.events = l3
    # Consume l3, but with a responder returning False -> abort
    await asyncio.sleep(time)   # Simulate interledger running

    assert len(i.transfers) == 0
    assert len(i.transfers_sent) == 0
    assert len(i.transfers_responded) == 0
    assert len(i.results_committing) == 0
    assert len(i.results_aborting) == 0
    assert len(i.results_commit) == 8
    assert len(i.results_abort) == 4

    i.stop()
    await task
