from sofie_asset_transfer.interledger import Interledger, Transfer, State
from typing import List
import pytest, time
import asyncio 
from unittest.mock import patch

test_receive = True
test_send = True
test_result = True
test_process = True
test_run = True

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

    async def get_transfers(self):
        result = []
        if len(self.events) > 0:
            result = self.events.copy()
            self.events.clear()
        return result
    
    async def commit_transfer(self, t: Transfer):
        return True

    async def abort_transfer(self, t: Transfer):
        return False


# Responder which getting positive result

class MockResponder:

    def __init__(self):
        self.events = []

    async def receive_transfer(self, t: Transfer):

        return 42


# Responder which getting negative result

class MockResponderAbort:

    async def receive_transfer(self, t: Transfer):

        return False



#
# Test receive_transfer
#

@pytest.mark.asyncio
async def test_interledger_receive_transfer():

    if test_receive:
        t = Transfer()
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

    if test_send:
        t = Transfer()
        i = Interledger(MockInitiator([]), MockResponder())

        i.transfers = [t]

        task = asyncio.ensure_future(i.send_transfer())
        assert task.done() == False
        await task

        assert i.pending == 1

        tr = i.transfers[0]
        assert tr.state == State.SENT
        assert asyncio.isfuture(tr.future)

        await tr.future
        assert tr.future.done() == True

#
# Test transfer_result
#
@pytest.mark.asyncio
async def test_interledger_transfer_result():

    if test_result:
        async def foo():
            return 42

        i = Interledger(MockInitiator([]), MockResponder())
        
        t = Transfer()
        t.state = State.SENT
        t.future = asyncio.ensure_future(foo())
        i.transfers_sent = [t]
        
        task = asyncio.ensure_future(i.transfer_result())
        assert task.done() == False
        await task

        tr = i.transfers_sent[0]
        assert tr.state == State.COMPLETED
        assert tr.result == 42


#
# Test transfer_result with a commit
#  - need ad-hoc commit future
#


@pytest.mark.asyncio
async def test_interledger_process_result_commit():

    if test_process:

        i = Interledger(MockInitiator([]), MockResponder())
        
        t = Transfer()
        t.state = State.COMPLETED
        t.result = True
        i.transfers_sent = [t]
        i.pending = 1
        
        task = asyncio.ensure_future(i.process_result())
        assert task.done() == False
        await task

        tr = i.transfers_sent[0]
        assert tr.state == State.PROCESSED
        assert len(i.results_commit) == 1
        assert len(i.results_abort) == 0
        assert i.pending == 0

#
# Test transfer_result with an abort
#

@pytest.mark.asyncio
async def test_interledger_process_result_abort():

    if test_process:

        i = Interledger(MockInitiator([]), MockResponder())
        
        t = Transfer()
        t.state = State.COMPLETED
        t.result == False
        i.transfers_sent = [t]
        i.pending = 1
        
        task = asyncio.ensure_future(i.process_result())
        assert task.done() == False
        await task

        tr = i.transfers_sent[0]
        assert tr.state == State.PROCESSED
        assert len(i.results_commit) == 0
        assert len(i.results_abort) == 1
        assert i.pending == 0


##############################

#
# Test run
#

@pytest.mark.asyncio
async def test_interledger_run_no_restore():

    if test_run:

        l1, l2, l3 = [], [], []
        for i in range(4):
            l1.append(Transfer())
            l2.append(Transfer())
            l3.append(Transfer())

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

        i.stop()
        await task

        assert len(i.transfers) == 12
        assert len(i.transfers_sent) == 12
        assert len(i.results_commit) == 8
        assert len(i.results_abort) == 4
        assert i.pending == 0