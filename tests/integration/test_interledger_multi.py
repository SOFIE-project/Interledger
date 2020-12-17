import pytest
import asyncio
from uuid import uuid4

from interledger.interledger import Interledger
from interledger.transfer import TransferStatus, TransferToMulti
from .utils import MockInitiator, MockMultiResponder, MockMultiResponderAbort


# from typing import List

# from unittest.mock import patch


# # # # Local view
# # #
# # #  MockInitiator <- Interledeger -> MockResponder(Abort)
# #


#
# Test receive_transfer
#
@pytest.mark.asyncio
async def test_interledger_multi_receive_transfer():

    t = TransferToMulti()
    t.payload = {}

    init = MockInitiator([t])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    interledger = Interledger(init, [resp1, resp2], True)
    # interledger.test_interrupt = True

    task = asyncio.ensure_future(interledger.receive_transfer())    
    assert task.done() == False
    l = await task

    assert init.events == []
    assert len(interledger.transfers) == 1
    assert l == 1
    assert interledger.transfers[0].state == TransferStatus.READY


#
# Test send_inquiry
#
@pytest.mark.asyncio
async def test_interledger_multi_send_inquiry():

    t = TransferToMulti()
    t.payload = {}
    t.payload['nonce'] = str(uuid4().int)
    t.payload['data'] =  b"dummy"

    init = MockInitiator([t])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)

    i.transfers = [t]

    # the processing to be observed
    task = asyncio.ensure_future(i.send_inquiry())
    assert task.done() == False
    await task

    assert len(i.transfers_inquired) == 1
 
    tr = i.transfers[0]
    assert tr.status == TransferStatus.INQUIRED

    assert len(tr.inquiry_tasks) == 2
    assert asyncio.isfuture(tr.inquiry_tasks[0])
    assert asyncio.isfuture(tr.inquiry_tasks[1])

    assert tr.inquiry_results == [None] * 2

    await asyncio.wait(tr.inquiry_tasks, return_when=asyncio.ALL_COMPLETED)
    assert tr.inquiry_tasks[0].done() == True
    assert tr.inquiry_tasks[1].done() == True


#
# Test transfer_inquiry
#
@pytest.mark.asyncio
async def test_interledger_multi_transfer_inquiry():

    async def foo():
        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}

    async def bar():
        return {"status": False, "tx_hash": "0xfail_tx_hash"}

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)

    t = TransferToMulti()
    t.status = TransferStatus.INQUIRED
    t.inquiry_tasks = [asyncio.ensure_future(foo()), asyncio.ensure_future(bar())]
    i.transfers_inquired = [t]
    
    # the processing to be observed
    task = asyncio.ensure_future(i.transfer_inquiry())
    assert task.done() == False
    await task

    assert len(i.transfers_inquired) == 0
    assert len(i.transfers_answered) == 1

    tr = i.transfers_answered[0]
    assert tr.state == TransferStatus.ANSWERED
    assert tr.inquiry_results[0]['status'] == True
    assert tr.inquiry_results[1]['status'] == False

    assert tr.inquiry_decision == True

    assert not i.transfers_inquired


#
# Test send_transfer
#
@pytest.mark.asyncio
async def test_interledger_multi_send_transfer():

    t = TransferToMulti()
    t.payload = {}
    t.payload['nonce'] = str(uuid4().int)
    t.payload['data'] =  b"dummy"
    t.inquiry_decision = True
    t.status = TransferStatus.ANSWERED

    init = MockInitiator([t])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)

    i.transfers = [t]
    i.transfers_answered = [t]

    # the processing to be observed
    task = asyncio.ensure_future(i.send_transfer())
    assert task.done() == False
    await task

    assert len(i.transfers_sent) == 1
 
    tr = i.transfers[0]
    assert tr.status == TransferStatus.SENT

    # verify the `send_tasks` instead of `send_task` works as expected
    assert tr.send_task is None
    assert asyncio.isfuture(tr.send_tasks[0])

    assert tr.results == [None] * 2

    assert tr in i.transfers_sent
    assert not i.transfers_answered

    await asyncio.wait(tr.send_tasks, return_when=asyncio.ALL_COMPLETED)
    assert tr.send_tasks[0].done() == True

    

#
# Test transfer_result
#
@pytest.mark.asyncio
async def test_interledger_multi_transfer_result():

    async def foo():
        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}

    async def bar():
        return {"status": False, "tx_hash": "0xfail_tx_hash"}

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)

    t = TransferToMulti()
    t.status = TransferStatus.SENT
    t.send_tasks = [asyncio.ensure_future(foo()), asyncio.ensure_future(bar())]
    i.transfers_sent = [t]
    
    # the processing to be observed
    task = asyncio.ensure_future(i.transfer_result())
    assert task.done() == False
    await task

    assert not i.transfers_sent
    assert t in i.transfers_responded

    tr = i.transfers_responded[0]
    assert tr.state == TransferStatus.RESPONDED
    assert tr.results[0]['status'] == True
    assert tr.results[1]['status'] == False


#
# Test process_result with a commit
#  - need ad-hoc commit future
#
@pytest.mark.asyncio
async def test_interledger_multi_process_result_commit():

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)
    
    t = TransferToMulti()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.status = TransferStatus.RESPONDED
    t.inquiry_decision = True
    t.results = [{"status": True}, {"status": False}]
    i.transfers_responded = [t]

    task = asyncio.ensure_future(i.process_result())
    assert task.done() == False
    await task

    assert len(i.results_committing) == 1
    tr = i.results_committing[0]
    assert tr.state == TransferStatus.CONFIRMING
    assert tr.results[0]['status'] == True
    assert tr.results[1]['status'] == False
    assert len(i.results_commit) == 0
    assert len(i.results_abort) == 0
    
    assert len(i.transfers_responded) == 0


#
# Test process_result with an abort
#
@pytest.mark.asyncio
async def test_interledger_multi_process_result_abort():

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)
    
    t = TransferToMulti()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.status = TransferStatus.RESPONDED
    t.inquiry_decision = True
    t.results = [{"status": False}, {"status": False}]
    i.transfers_responded = [t]
    
    task = asyncio.ensure_future(i.process_result())
    assert task.done() == False
    await task

    tr = i.results_aborting[0]
    assert tr.state == TransferStatus.CONFIRMING
    assert tr.results[0]['status'] == False
    assert tr.results[1]['status'] == False
    assert len(i.results_commit) == 0
    assert len(i.results_abort) == 0

    assert len(i.transfers_responded) == 0


#
# Test process_result with inquiry rejection
#
@pytest.mark.asyncio
async def test_interledger_multi_process_result_inquiry_rejection():

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)
    
    t = TransferToMulti()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.status = TransferStatus.RESPONDED
    t.inquiry_decision = False
    t.results = [{"status": True}, {"status": True}] # set it even to true should not affect
    i.transfers_responded = [t]
    
    task = asyncio.ensure_future(i.process_result())
    assert task.done() == False
    await task

    tr = i.results_aborting[0]
    assert tr.state == TransferStatus.CONFIRMING
    assert tr.results[0]['status'] == True
    assert tr.results[1]['status'] == True
    assert len(i.results_commit) == 0
    assert len(i.results_abort) == 0

    assert len(i.transfers_responded) == 0

#
# Test confirm_transfer with a commit
#
@pytest.mark.asyncio
async def test_interledger_multi_confirm_transfer_commit():
    async def foo():
        return {'commit_status': True,
                'commit_tx_hash': '0x333'}

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True)

    t = TransferToMulti()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.results = []
    t.status = TransferStatus.CONFIRMING
    t.inquiry_decision = True
    t.confirm_task = asyncio.ensure_future(foo())
    i.results_committing = [t]
    
    task = asyncio.ensure_future(i.confirm_transfer())
    assert task.done() == False
    await task

    res = i.results_commit[0]
    assert t.status == TransferStatus.FINALIZED
    assert res['commit_status'] == True
    assert res['commit_tx_hash'] == '0x333'
    assert len(i.results_commit) == 1
    assert len(i.results_abort) == 0

    assert len(i.results_committing) == 0


#
# Test confirm_transfer with an abort
#
@pytest.mark.asyncio
async def test_interledger_multi_confirm_transfer_abort():
    async def foo():
        return {'abort_status': True,
                'abort_tx_hash': '0x444'}

    init = MockInitiator([])
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    i = Interledger(init, [resp1, resp2], True, 1)

    t = TransferToMulti()
    t.payload = {}
    t.payload['id'] = str(uuid4().int)
    t.results = []
    t.status = TransferStatus.CONFIRMING
    t.inquiry_decision = True
    t.confirm_task = asyncio.ensure_future(foo())
    i.results_aborting = [t]
    
    task = asyncio.ensure_future(i.confirm_transfer())
    assert task.done() == False
    await task

    res = i.results_abort[0]
    assert t.status == TransferStatus.FINALIZED
    assert res['abort_status'] == True
    assert res['abort_tx_hash'] == '0x444'
    assert len(i.results_abort) == 1
    assert len(i.results_commit) == 0

    assert len(i.results_aborting) == 0

##############################

#
# Test run
#
    

@pytest.mark.asyncio
async def test_interledger_ledger_run_with_cleanup():

    l1, l2, l3 = [], [], []
    for i in range(4):
        t1, t2, t3 = TransferToMulti(), TransferToMulti(), TransferToMulti()
        t1.payload, t2.payload, t3.payload = {}, {}, {}
        t1.payload['nonce'], t1.payload['id'], t1.payload['data'] = str(uuid4().int), '1', b"dummy1"
        t2.payload['nonce'], t2.payload['id'], t2.payload['data'] = str(uuid4().int), '2', b"dummy2"
        t3.payload['nonce'], t3.payload['id'], t3.payload['data'] = str(uuid4().int), '3', b"dummy3"
        l1.append(t1)
        l2.append(t2)
        l3.append(t3)

    init = MockInitiator(l1)
    resp1 = MockMultiResponder()
    resp2 = MockMultiResponder()
    resp3 = MockMultiResponderAbort()
    i = Interledger(init, [resp1, resp2, resp3], True, 2)

    task = asyncio.ensure_future(i.run())

    time = 1.0
    # Consume l1
    await asyncio.sleep(time)   # Simulate interledger running

    # New events
    init.events = l2
    # Consume l2
    await asyncio.sleep(time)   # Simulate interledger running

    # New events
    i.responders[1] = MockMultiResponderAbort()
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
