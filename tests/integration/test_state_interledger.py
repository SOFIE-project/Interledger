from sofie_asset_transfer.interledger import StateInterledger, Transfer, State
from sofie_asset_transfer.state_interfaces import StateInitiator, StateResponder
from typing import List
import pytest, time
import asyncio 
from unittest.mock import patch

#
# Test pending transfer restore
#

def test_interledger_pending_transfers_ready():

    initiator = StateInitiator()
    responder = StateResponder()
    
    package = "sofie_asset_transfer.state_interfaces"
    with patch(package+".StateInitiator.query_by_state", return_value=[123, 1234]) as mock_query_init:
        with patch(package+".StateResponder.query_by_state", return_value=[123, 12345]) as mock_query_resp:
            with patch("sofie_asset_transfer.interledger.StateInterledger", "__init__", lambda s, i, r: None):
                # Patch the init method, otherwise it will call restore_* and fail

                interledger = StateInterledger(initiator, responder)
                interledger.restore_pending_transfers_ready()

                assert len(interledger.transfers) == 1
                assert interledger.transfers[0].data["assetId"] == 123
                assert interledger.transfers[0].state == State.READY

def test_interledger_pending_transfers_sent():

    initiator = StateInitiator()
    responder = StateResponder()

    package = "sofie_asset_transfer.state_interfaces"
    with patch(package+".StateInitiator.query_by_state", return_value=[123, 1234]) as mock_query_init:
        with patch(package+".StateResponder.query_by_state", return_value=[123, 12345]) as mock_query_resp:
            with patch("sofie_asset_transfer.interledger.StateInterledger", "__init__", lambda s, i, r: None):
                # Patch the init method, otherwise it will call restore_* and fail

                interledger = StateInterledger(initiator, responder)
                interledger.restore_pending_transfers_sent()

                assert len(interledger.transfers_sent) == 1
                assert interledger.transfers_sent[0].data["assetId"] == 123
                assert interledger.transfers_sent[0].state == State.RESPONDED

#
# Test run
#   1- With initial restore ready
#   2- With initial restore sent
#

@pytest.mark.asyncio
async def test_interledger_run_with_restore_ready():

    base = "sofie_asset_transfer"
    package = base+".interledger.StateInterledger"

    # Create a new transfer
        # for protocol PoW, it should have state (TransferOut | Here)
    t = Transfer()
    t.data = {}
    t.data["assetId"] = 123
    
    with patch(package+".restore_pending_transfers_ready", return_value=[t]) as mock_ready:
        with patch(package+".restore_pending_transfers_sent", return_value=[]) as mock_sent:

            interledger = StateInterledger(StateInitiator(), StateResponder()) 

            init = base+".state_interfaces.StateInitiator"
            resp = base+".state_interfaces.StateResponder"
            get_future = asyncio.Future()
            receive_future = asyncio.Future()
            commit_future = asyncio.Future()
            get_future.set_result([])
            receive_future.set_result({"status": True})
            commit_future.set_result(True)

            with patch(init+".get_transfers", return_value=get_future) as mock_get_transfers:
                with patch(resp+".receive_transfer", return_value=receive_future) as mock_receive_transfer:
                    with patch(init+".commit_transfer", return_value=commit_future) as mock_commit:
                        with patch(base+".interledger.Interledger.cleanup") as mock_cleanup:
                            # mock cleanup to check the transfer reaches the end

                            time = 1
                            task = asyncio.ensure_future(interledger.run())
                            await asyncio.sleep(time)
                            interledger.stop()
                            await task

                            assert len(interledger.transfers) == 1
                            assert len(interledger.transfers_sent) == 1
                            assert len(interledger.results_commit) == 1
                            assert interledger.pending == 0


@pytest.mark.asyncio
async def test_interledger_run_with_restore_sent():

    base = "sofie_asset_transfer"
    package = base+".interledger.StateInterledger"

    # Create a transfer already half processed
        # for protocol PoW, it should have state (TransferOut | NotHere)
    t = Transfer()
    t.data = {}
    t.data["assetId"] = 123
    t.state = State.RESPONDED
    t.future = asyncio.Future()
    t.future.set_result({"status": True})
    t.result = {"status": True}

    with patch(package+".restore_pending_transfers_ready", return_value=[]) as mock_ready:
        with patch(package+".restore_pending_transfers_sent", return_value=[t]) as mock_sent:

            interledger = StateInterledger(StateInitiator(), StateResponder())

            init = base+".state_interfaces.StateInitiator"
            resp = base+".state_interfaces.StateResponder"
            get_future = asyncio.Future()
            receive_future = asyncio.Future()
            commit_future = asyncio.Future()
            get_future.set_result([])
            receive_future.set_result({"status": True})
            commit_future.set_result(True)

            with patch(init+".get_transfers", return_value=get_future) as mock_get_transfers:
                with patch(resp+".receive_transfer", return_value=receive_future) as mock_receive_transfer:
                    with patch(init+".commit_transfer", return_value=commit_future) as mock_commit:
                        with patch(base+".interledger.Interledger.cleanup") as mock_cleanup:
                            # mock cleanup to check the transfer reaches the end

                            time = 1
                            task = asyncio.ensure_future(interledger.run())
                            await asyncio.sleep(time)
                            interledger.stop()
                            await task

                            assert len(interledger.transfers_sent) == 1
                            assert len(interledger.results_commit) == 1
                            assert interledger.pending == 0
