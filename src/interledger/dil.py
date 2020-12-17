from typing import Union, List
from uuid import uuid4
import asyncio

from .adapter.interfaces import Initiator, Responder, ILStateManager, LedgerType
from .interledger import Interledger
from .transfer import TransferStatus


class DecentralizedInterledger(Interledger):
    """
    Class definition of decentralized extended version of Interledger instance
    """

    def __init__(self, initiator: Initiator,
                 responder: Union[Responder, List],
                 state_manager: ILStateManager,
                 multi: bool = False,
                 threshold: int = 1):

        super().__init__(initiator, responder, multi, threshold)
        self.state_manager = state_manager

    # Trigger
    async def receive_transfer(self):
        transfers_raw = await self.initiator.listen_for_events()
        valid_count = 0

        # create entries at state layer
        if transfers_raw:
            for transfer in transfers_raw:
                id = transfer.payload['id']
                transfer.payload['nonce'] = str(uuid4().int)
                res = await self.state_manager.create_entry(id, transfer)

                # TODO: signal acceptance after filtering algorithm
                await self.state_manager.signal_send_acceptance(id) # for now, OK for all

                valid_count += res

        # prepare entries of transfers that are ready
        await self.state_manager.receive_entry_events(TransferStatus.READY)

        return valid_count

    # Action
    async def send_transfer(self):
        for transfer in self.state_manager.transfers_ready:
            payload = transfer.payload
            id, nonce, data = payload['id'], payload['nonce'], payload['data']

            if transfer.status == TransferStatus.READY:
                transfer.status = TransferStatus.SENT
                transfer.send_task = asyncio.ensure_future(
                    self.responder.send_data(nonce, data))

                # cached for transfer_result
                self.transfers_sent.append(transfer)
                await self.state_manager.update_entry(id, TransferStatus.SENT, transfer)

        self.state_manager.transfers_ready = [t for t in self.state_manager.transfers_ready
                                              if t.status == TransferStatus.READY]

    # Trigger
    async def transfer_result(self):
        send_tasks = [transfer.send_task for transfer in self.transfers_sent]
        if not send_tasks:
            return

        await asyncio.wait(send_tasks, return_when=asyncio.FIRST_COMPLETED)
        for transfer in self.transfers_sent:
            if transfer.status == TransferStatus.SENT and transfer.send_task.done():
                id = transfer.payload['id']
                transfer.result = transfer.send_task.result()

                transfer.status = TransferStatus.RESPONDED
                await self.state_manager.update_entry(id, TransferStatus.RESPONDED, transfer)

        # # update records
        self.transfers_sent = [
            transfer for transfer in self.transfers_sent if transfer.status == TransferStatus.SENT]
        await self.state_manager.receive_entry_events(TransferStatus.RESPONDED)

    # Action
    async def process_result(self):
        for transfer in self.state_manager.transfers_responded:
            if transfer.status == TransferStatus.RESPONDED:
                id = transfer.payload['id']

                if transfer.result["status"]:  # commit the transfer from initiator
                    # If the Responder ledger is KSI, pass the KSI id (stored in
                    # tx_hash field of transfer) to the Initiator's commit function
                    if self.responder.ledger_type == LedgerType.KSI:
                        transfer.confirm_task = asyncio.ensure_future(
                            self.initiator.commit_sending(id, transfer.result['tx_hash'].encode()))
                    else:
                        transfer.confirm_task = asyncio.ensure_future(
                            self.initiator.commit_sending(id))
                    self.results_committing.append(transfer)
                else:  # abort the transfer from initiator
                    reason = 2  # ErrorCode.TRANSACTION_FAILURE
                    transfer.confirm_task = asyncio.ensure_future(
                        self.initiator.abort_sending(id, reason))
                    self.results_aborting.append(transfer)

                transfer.status = TransferStatus.CONFIRMING
                await self.state_manager.update_entry(id, TransferStatus.CONFIRMING, transfer)

        # update records
        self.state_manager.transfers_responded = [transfer for transfer in self.state_manager.transfers_responded
                                                  if transfer.status == TransferStatus.RESPONDED]

    async def confirm_transfer(self):
        confirm_tasks = [
            transfer.confirm_task for transfer in self.results_committing + self.results_aborting]
        if not confirm_tasks:
            return
        await asyncio.wait(confirm_tasks, return_when=asyncio.FIRST_COMPLETED)

        for transfer in self.results_committing:
            if transfer.status == TransferStatus.CONFIRMING and transfer.confirm_task.done():
                id = transfer.payload['id']
                commit_result = transfer.confirm_task.result()

                transfer.status = TransferStatus.FINALIZED
                transfer.result['commit_status'] = commit_result['commit_status']
                transfer.result['commit_tx_hash'] = commit_result['commit_tx_hash']
                if 'commit_error_code' in commit_result:
                    transfer.result['commit_error_code'] = commit_result['commit_error_code']
                    transfer.result['commit_message'] = commit_result['commit_message']

                await self.state_manager.update_entry(id, TransferStatus.FINALIZED, transfer)
                self.results_commit.append(transfer)

        self.results_committing = [
            transfer for transfer in self.results_committing if transfer.status == TransferStatus.CONFIRMING]

        for transfer in self.results_aborting:
            if transfer.status == TransferStatus.CONFIRMING and transfer.confirm_task.done():
                id = transfer.payload['id']
                abort_result = transfer.confirm_task.result()

                transfer.status = TransferStatus.FINALIZED
                transfer.result['abort_status'] = abort_result['abort_status']
                transfer.result['abort_tx_hash'] = abort_result['abort_tx_hash']
                if 'abort_error_code' in abort_result:
                    transfer.result['abort_error_code'] = abort_result['abort_error_code']
                    transfer.result['abort_message'] = abort_result['abort_message']

                await self.state_manager.update_entry(id, TransferStatus.FINALIZED, transfer)
                self.results_abort.append(transfer)

        self.results_aborting = [
            transfer for transfer in self.results_aborting if transfer.status == TransferStatus.CONFIRMING]
