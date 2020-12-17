
import pytest
import asyncio
from copy import deepcopy
from uuid import uuid4

from interledger.transfer import TransferStatus, Transfer
from interledger.adapter.state_manager import FabricILStateManager
from .utils import MockInitiator, MockResponder, MockResponderAbort
from interledger.dil import DecentralizedInterledger

# Overview
# MockInitiator <- Interledeger -> MockResponder
#               (HF state manager)


# test DIL receive transfer
@pytest.mark.asyncio
async def test_dil_receive_transfer(config):
    # initialize
    t = Transfer()
    t.payload = {'id': '001', 'data': '0xdummy_data'}

    init = MockInitiator([t])
    resp = MockResponder()

    net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name = config
    state_manager = FabricILStateManager(net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    dil = DecentralizedInterledger(init, resp, state_manager)

    # assert not dil.state_manager.local_transfers
    # assert not dil.state_manager.transfers_ready
    # assert not dil.state_manager.transfers_responded

    # # start
    # task = asyncio.ensure_future(dil.receive_transfer())
    # assert task.done() == False
    # l = await task

    # # check local transfers populated
    # assert dil.state_manager.local_transfers
    # assert len(dil.state_manager.local_transfers) == 1

    # local_transfer = dil.state_manager.local_transfers['001']

    # assert local_transfer.payload['id']
    # assert local_transfer.payload['nonce']
    # nonce = local_transfer.payload['nonce']
    # assert local_transfer.payload['data'] == '0xdummy_data'

    # assert local_transfer.status == TransferStatus.READY

    # # check transfer ready
    # assert dil.state_manager.transfers_ready
    # assert len(dil.state_manager.transfers_ready) == 1

    # transfer_ready = dil.state_manager.transfers_ready[0]

    # assert transfer_ready.payload['id'] == '001'
    # assert transfer_ready.payload['nonce'] == nonce
    # assert transfer_ready.payload['data'] == '0xdummy_data'

    # assert transfer_ready.status == TransferStatus.READY

    # # TODO: test filtering of incoming transfer

    # assert not dil.state_manager.transfers_responded


# # test DIL send transfer
# @pytest.mark.asyncio
# async def test_dil_send_transfer():
#     # initialize
#     t = Transfer()
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)
#     t.send_accepted = True

#     init = MockInitiator([t])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)

#     dil.transfers = [t]
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}
#     dil.state_manager.transfers_ready = [t]

#     assert len(dil.transfers_sent) == 0

#     # start
#     task = asyncio.ensure_future(dil.send_transfer())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.payload['id']
#     assert local_transfer.payload['nonce']
#     assert local_transfer.payload['data'] == '0xdummy_data'

#     assert local_transfer.status == TransferStatus.SENT

#     # check for transfer sent
#     assert len(dil.transfers_sent) == 1

#     transfer_sent = dil.transfers[0]
#     assert transfer_sent.status == TransferStatus.SENT
#     assert asyncio.isfuture(transfer_sent.send_task)

#     await transfer_sent.send_task
#     assert transfer_sent.send_task.done() == True


# # Test DIL transfer result
# @pytest.mark.asyncio
# async def test_dil_transfer_result():
#     # initialize
#     t = Transfer()
#     t.status = TransferStatus.SENT
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)

#     init = MockInitiator([])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}

#     async def foo():
#         return 42

#     t.send_task = asyncio.ensure_future(foo())
#     dil.transfers = [t]
#     dil.transfers_sent = [t]

#     # start
#     task = asyncio.ensure_future(dil.transfer_result())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.status == TransferStatus.RESPONDED
#     assert local_transfer.result == 42

#     # check for transfer responded
#     assert len(dil.state_manager.transfers_responded) == 1
#     transfer_responded = dil.transfers[0]

#     assert transfer_responded.status == TransferStatus.RESPONDED
#     assert transfer_responded.result == 42

#     assert not dil.transfers_sent


# # Test DIL process result for commit
# @pytest.mark.asyncio
# async def test_dil_process_result_commit():
#     # initialize
#     t = Transfer()
#     t.status = TransferStatus.RESPONDED
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)
#     t.result = {'status': True}

#     init = MockInitiator([])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}
#     dil.state_manager.transfers_responded = [t]

#     async def foo():
#         return 42

#     t.confirm_task = asyncio.ensure_future(foo())
#     dil.transfers = [t]

#     # start
#     task = asyncio.ensure_future(dil.process_result())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.status == TransferStatus.CONFIRMING
#     assert local_transfer.result['status'] == True

#     # check for transfer confirming
#     assert len(dil.results_committing) == 1
#     result_confirming = dil.results_committing[0]

#     assert result_confirming.status == TransferStatus.CONFIRMING
#     assert result_confirming.result['status'] == True
#     assert asyncio.isfuture(result_confirming.confirm_task)

#     assert len(dil.results_commit) == 0
#     assert len(dil.results_abort) == 0

#     await result_confirming.confirm_task
#     assert result_confirming.confirm_task.done() == True

#     assert not dil.state_manager.transfers_responded


# # Test DIL process result for abort
# @pytest.mark.asyncio
# async def test_dil_process_result_abort():
#     # initialize
#     t = Transfer()
#     t.status = TransferStatus.RESPONDED
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)
#     t.result = {'status': False}

#     init = MockInitiator([])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}
#     dil.state_manager.transfers_responded = [t]

#     async def foo():
#         return 42

#     t.confirm_task = asyncio.ensure_future(foo())
#     dil.transfers = [t]

#     # start
#     task = asyncio.ensure_future(dil.process_result())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.status == TransferStatus.CONFIRMING
#     assert local_transfer.result['status'] == False

#     # check for transfer confirming
#     assert len(dil.results_aborting) == 1
#     result_confirming = dil.results_aborting[0]

#     assert result_confirming.status == TransferStatus.CONFIRMING
#     assert result_confirming.result['status'] == False
#     assert asyncio.isfuture(result_confirming.confirm_task)

#     assert len(dil.results_commit) == 0
#     assert len(dil.results_abort) == 0

#     await result_confirming.confirm_task
#     assert result_confirming.confirm_task.done() == True

#     assert len(dil.state_manager.transfers_responded) == 0


# # Test DIL confirm_transfer with a commit
# @pytest.mark.asyncio
# async def test_dil_confirm_transfer_commit():
#     # initialize
#     t = Transfer()
#     t.status = TransferStatus.CONFIRMING
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)
#     t.result = {}

#     init = MockInitiator([])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}

#     async def foo():
#         return {'commit_status': True,
#                 'commit_tx_hash': '0x333'}

#     t.confirm_task = asyncio.ensure_future(foo())
#     dil.results_committing = [t]

#     # start
#     task = asyncio.ensure_future(dil.confirm_transfer())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.status == TransferStatus.FINALIZED
#     assert local_transfer.result['commit_status'] == True

#     # check for transfer confirming
#     assert len(dil.results_commit) == 1
#     result_confirming = dil.results_commit[0]

#     assert result_confirming.status == TransferStatus.FINALIZED
#     assert result_confirming.result['commit_status'] == True
#     assert result_confirming.result['commit_tx_hash'] == '0x333'
#     assert asyncio.isfuture(result_confirming.confirm_task)

#     assert len(dil.results_committing) == 0
#     assert len(dil.results_abort) == 0


# # Test DIL confirm_transfer with a abort
# @pytest.mark.asyncio
# async def test_dil_confirm_transfer_abort():
#     # initialize
#     t = Transfer()
#     t.status = TransferStatus.CONFIRMING
#     t.payload = {'id': '001', 'data': '0xdummy_data'}
#     t.payload['nonce'] = str(uuid4().int)
#     t.result = {}

#     init = MockInitiator([])
#     resp = MockResponder()
#     state_manager = LocalILStateManger()

#     dil = DecentralizedInterledger(init, resp, state_manager)
#     dil.state_manager.local_transfers = {'001': deepcopy(t)}

#     async def foo():
#         return {'abort_status': True,
#                 'abort_tx_hash': '0x444'}

#     t.confirm_task = asyncio.ensure_future(foo())
#     dil.results_aborting = [t]

#     # start
#     task = asyncio.ensure_future(dil.confirm_transfer())
#     assert task.done() == False
#     await task

#     # check local transfers updated
#     assert dil.state_manager.local_transfers
#     assert len(dil.state_manager.local_transfers) == 1

#     local_transfer = dil.state_manager.local_transfers['001']

#     assert local_transfer.status == TransferStatus.FINALIZED
#     assert local_transfer.result['abort_status'] == True

#     # check for transfer confirming
#     assert len(dil.results_abort) == 1
#     result_confirming = dil.results_abort[0]

#     assert result_confirming.status == TransferStatus.FINALIZED
#     assert result_confirming.result['abort_status'] == True
#     assert result_confirming.result['abort_tx_hash'] == '0x444'
#     assert asyncio.isfuture(result_confirming.confirm_task)

#     assert len(dil.results_aborting) == 0
#     assert len(dil.results_commit) == 0


# @pytest.mark.asyncio
# async def test_dil_run():

#     l1, l2, l3 = [], [], []
#     for i in range(2):
#         t1, t2, t3 = Transfer(), Transfer(), Transfer()
#         t1.payload, t2.payload, t3.payload = {}, {}, {}
#         t1.payload['nonce'], t1.payload['id'], t1.payload['data'] = str(
#             uuid4().int), '1', b"dummy1"
#         t2.payload['nonce'], t2.payload['id'], t2.payload['data'] = str(
#             uuid4().int), '2', b"dummy2"
#         t3.payload['nonce'], t3.payload['id'], t3.payload['data'] = str(
#             uuid4().int), '3', b"dummy3"
#         l1.append(t1)
#         l2.append(t2)
#         l3.append(t3)

#     init = MockInitiator(l1)
#     resp = MockResponder()
#     state_manager = LocalILStateManger()
#     dil = DecentralizedInterledger(init, resp, state_manager)

#     task = asyncio.ensure_future(dil.run())

#     time = 0.5
#     # Consume l1
#     await asyncio.sleep(time)   # Simulate interledger running

#     # New events
#     init.events = l2
#     # Consume l2
#     await asyncio.sleep(time)   # Simulate interledger running

#     # New events
#     dil.responder = MockResponderAbort()
#     init.events = l3
#     # Consume l3, but with a responder returning False -> abort
#     await asyncio.sleep(time)   # Simulate interledger running

#     assert len(dil.transfers) == 0
#     assert len(dil.transfers_sent) == 0
#     assert len(dil.transfers_responded) == 0
#     assert len(dil.results_committing) == 0
#     assert len(dil.results_aborting) == 0
#     # below should not equal to 4, since transfer with repeated id will be rejected
#     assert len(dil.results_commit) == 2
#     # below should not equal to 2, since transfer with repeated id will be rejected
#     assert len(dil.results_abort) == 1

#     dil.stop()
#     await task
