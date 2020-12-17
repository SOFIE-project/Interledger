import asyncio
from typing import Union, List
from uuid import uuid4

from .adapter.interfaces import Initiator, Responder, MultiResponder, ErrorCode, LedgerType
from .transfer import TransferStatus


class Interledger(object):
    """
    Class definition of an interledger component, which is composed by an Initiator and a Responder to implement the data transfer operation.
    """
    def __init__(self, initiator: Initiator, responder: Union[Responder, List], multi: bool=False, threshold: int=1):
        """Constructor
        :param object initiator: The Initiator object
        :param object responder: The Responder object by default, list of Responder objects in multi-ledger mode
        :param bool multi: whether the multi-ledger mode is enabled
        :param int threshold: threshold number of minimum requirement for positive responses from all responders
        """

        # multi-ledger mode
        self.multi = multi

        # initiator and responder
        self.initiator = initiator
        if not self.multi:
            self.responder = responder
            self.responders = None
        else:
            self.responder = None
            self.responders = responder
            # check multi-responder
            for resp in self.responders:
                if not isinstance(resp, MultiResponder):
                    raise TypeError("MultiResponder required in multi-ledger mode")

        if not self.multi:
            self.threshold = 1
        else:
            if threshold < 0 or threshold > len(self.responders):
                raise ValueError("Invalid threshold number")
            self.threshold = threshold

        # transfer ralated
        self.transfers = []
        
        if not self.multi:
            self.transfers_inquired = None
            self.transfers_answered = None
        else:
            self.transfers_inquired = []
            self.transfers_answered = []

        self.transfers_sent = []
        self.transfers_responded = []

        self.results_committing = []
        self.results_commit = []

        self.results_aborting = []
        self.results_abort = []

        # initial state is down
        self.up = False
        
    async def run(self):
        """Run the interledger.
        Wait for new transfers from the Initiator, forward them to the Responder and finalize the protocol with the Intiator.
        """
        self.up = True
        while self.up:
            # Triggers
            receive = asyncio.ensure_future(self.receive_transfer())
            if not self.transfers_inquired \
               and not self.transfers_sent \
               and not self.results_committing \
               and not self.results_aborting:
                await receive
            else:
                answer = asyncio.ensure_future(self.transfer_inquiry())
                result = asyncio.ensure_future(self.transfer_result())
                confirm = asyncio.ensure_future(self.confirm_transfer())
                asyncio.wait([receive, answer, result, confirm], return_when=asyncio.FIRST_COMPLETED)

            # Actions
            inquiry = asyncio.ensure_future(self.send_inquiry())
            send = asyncio.ensure_future(self.send_transfer())
            process = asyncio.ensure_future(self.process_result())
            await send
            await process

            # clean up
            self.cleanup()

        # TODO Add some closing procedure

    def stop(self):
        """Stop the interledger run() operation
        """
        self.up = False

        self.transfers = []

        self.transfers_sent = []
        self.transfers_responded = []

        self.results_committing = []
        self.results_commit = []

        self.results_aborting = []
        self.results_abort = []

    # Trigger
    async def receive_transfer(self):
        """Receive the list of transfers from the Initiator. 
           This operation blocks until it receives at least one transfer.
        """
        transfers = await self.initiator.listen_for_events()
        if transfers:
            # include random nonce in transfer paylaod
            for transfer in transfers:
                transfer.payload['nonce'] = str(uuid4().int)
            self.transfers.extend(transfers)
        return len(transfers)

    # Action (used by multi-ledger mode only)
    async def send_inquiry(self):
        """Used in multi-ledger mode, forward transfer inquiry to responders.
        """
        if not self.multi:
            return
        for transfer in self.transfers:
            if transfer.status == TransferStatus.READY:
                transfer.status = TransferStatus.INQUIRED
                nonce, data = transfer.payload['nonce'], transfer.payload['data']
                transfer.inquiry_tasks = [asyncio.ensure_future( \
                    resp.send_data_inquire(nonce, data)) \
                    for resp in self.responders]
                transfer.inquiry_results = [None] * len(self.responders)
                self.transfers_inquired.append(transfer)

    # Trigger (used by multi-ledger mode only)
    async def transfer_inquiry(self):
        """Stores the inquiry results coming back to connected responders.
        """
        if not self.multi: 
            return

        inquiry_tasks = []
        for transfer in self.transfers_inquired:
            inquiry_tasks.extend(transfer.inquiry_tasks)
        if not inquiry_tasks: 
            return

        await asyncio.wait(inquiry_tasks, return_when=asyncio.ALL_COMPLETED)

        for transfer in self.transfers_inquired:
            transfer.inquiry_results = [t.result() if t.done() else None for t in transfer.inquiry_tasks]
            status = [r['status'] for r in transfer.inquiry_results]
            transfer.inquiry_decision = status.count(True) >= self.threshold
            transfer.status = TransferStatus.ANSWERED
            self.transfers_answered.append(transfer)

        # update records
        self.transfers_inquired = [transfer for transfer in self.transfers_inquired if transfer.status == TransferStatus.INQUIRED]


    # Action
    async def send_transfer(self):
        """Forward the stored transfers to the Responder.
        """
        if not self.multi:
            for transfer in self.transfers:
                # generate nonce
                nonce, data = transfer.payload['nonce'], transfer.payload['data']

                if transfer.status == TransferStatus.READY:
                    transfer.status = TransferStatus.SENT                    
                    # send data to destination ledger
                    transfer.send_task = asyncio.ensure_future(self.responder.send_data(nonce, data))
                    self.transfers_sent.append(transfer)

        else: # multi-ledger mode
            for transfer in self.transfers_answered:
                # generate nonce
                nonce, data = transfer.payload['nonce'], transfer.payload['data']

                if transfer.status == TransferStatus.ANSWERED:
                    transfer.status = TransferStatus.SENT
                    if transfer.inquiry_decision: # inquiry agreed
                        transfer.send_tasks = [asyncio.ensure_future( \
                            resp.send_data(nonce, data)) \
                            for resp in self.responders]
                    else: # inquiry rejected
                        transfer.send_tasks = [asyncio.ensure_future( \
                            resp.abort_send_data(nonce, 5)) \
                            for resp in self.responders] # reason = 5 for INQUIRY_REJECT
                    transfer.results = [None] * len(self.responders)
                    self.transfers_sent.append(transfer)
            
            # update records
            self.transfers_answered = [transfer for transfer in self.transfers_answered if transfer.status == TransferStatus.ANSWERED]


    # Trigger
    async def transfer_result(self):
        """Store the results of the transfers sent to the Responder. 
           This operation blocks until at least one future has been completed.
        """
        if not self.multi:
            send_tasks = [transfer.send_task for transfer in self.transfers_sent]
        else:
            send_tasks = []
            for transfer in self.transfers_sent:
                send_tasks.extend(transfer.send_tasks)

        if not send_tasks:
            return

        if not self.multi:
            await asyncio.wait(send_tasks, return_when=asyncio.FIRST_COMPLETED)
            for transfer in self.transfers_sent:
                if transfer.status == TransferStatus.SENT and transfer.send_task.done():
                    transfer.result = transfer.send_task.result()
                    transfer.status = TransferStatus.RESPONDED
                    self.transfers_responded.append(transfer)

        else:
            await asyncio.wait(send_tasks, return_when=asyncio.ALL_COMPLETED)
            for transfer in self.transfers_sent:
                transfer.results = [t.result() if t.done() else None for t in transfer.send_tasks]
                transfer.status = TransferStatus.RESPONDED
                self.transfers_responded.append(transfer)
                
        # update records
        self.transfers_sent = [transfer for transfer in self.transfers_sent if transfer.status == TransferStatus.SENT]

    # Action
    async def process_result(self):
        """Process the result of the responder: trigger the commit() or the abort()
           operation of the Initiator to confirm the status of the transfer.
        """
        if not self.multi:
            for transfer in self.transfers_responded:
                if transfer.status == TransferStatus.RESPONDED:
                    id = transfer.payload['id']

                    if transfer.result["status"]: # commit the transfer from initiator
                        # If the Responder ledger is KSI, pass the KSI id (stored in 
                        # tx_hash field of transfer) to the Initiator's commit function
                        if self.responder.ledger_type == LedgerType.KSI:
                            transfer.confirm_task = asyncio.ensure_future(
                                self.initiator.commit_sending(id, transfer.result['tx_hash'].encode()))
                        else:
                            transfer.confirm_task = asyncio.ensure_future(
                                self.initiator.commit_sending(id))
                        self.results_committing.append(transfer)
                    else: # abort the transfer from initiator
                        reason =  2 # ErrorCode.TRANSACTION_FAILURE
                        transfer.confirm_task = asyncio.ensure_future(self.initiator.abort_sending(id, reason))
                        self.results_aborting.append(transfer)

                    transfer.status = TransferStatus.CONFIRMING
        
        else: # multi-ledger mode
            for transfer in self.transfers_responded:
                if transfer.status == TransferStatus.RESPONDED:
                    id = transfer.payload['id']

                    if transfer.inquiry_decision:
                        status = [r['status'] for r in transfer.results if r and 'status' in r]
                        if status.count(True) >= self.threshold:
                            transfer.confirm_task = asyncio.ensure_future(
                                self.initiator.commit_sending(id))
                            self.results_committing.append(transfer)
                        else:
                            reason =  2 # ErrorCode.TRANSACTION_FAILURE
                            transfer.confirm_task = asyncio.ensure_future(
                                self.initiator.abort_sending(id, reason))
                            self.results_aborting.append(transfer)
                    
                    else: # inquiry rejected
                        reason = 5 # ErrorCode.INQUIRY_REJECT
                        transfer.confirm_task = asyncio.ensure_future(
                            self.initiator.abort_sending(id, reason))
                        self.results_aborting.append(transfer)

                transfer.status = TransferStatus.CONFIRMING

        # update records
        self.transfers_responded = [transfer for transfer in self.transfers_responded \
            if transfer.status == TransferStatus.RESPONDED]


    async def confirm_transfer(self):
        """Confirm the status of transfer as either commit or abort based on the initiator operations, to complete the protocol
        """
        confirm_tasks = [transfer.confirm_task for transfer in self.results_committing + self.results_aborting]
        if not confirm_tasks:
            return
        await asyncio.wait(confirm_tasks, return_when=asyncio.FIRST_COMPLETED)

        for transfer in self.results_committing:
            if transfer.status == TransferStatus.CONFIRMING and transfer.confirm_task.done():
                # retrieve confirm result and update state
                commit_result = transfer.confirm_task.result()
                transfer.status = TransferStatus.FINALIZED
                # record confirm result
                transfer.result['commit_status'] = commit_result['commit_status']
                transfer.result['commit_tx_hash'] = commit_result['commit_tx_hash']
                if 'commit_error_code' in commit_result:
                    transfer.result['commit_error_code'] = commit_result['commit_error_code']
                    transfer.result['commit_message'] = commit_result['commit_message']
                # update records
                self.results_commit.append(transfer.result)
        self.results_committing = [transfer for transfer in self.results_committing if transfer.status == TransferStatus.CONFIRMING]

        for transfer in self.results_aborting:
            if transfer.status == TransferStatus.CONFIRMING and transfer.confirm_task.done():
                # retrieve confirm result and update state
                abort_result = transfer.confirm_task.result()
                transfer.status = TransferStatus.FINALIZED
                # record abort result
                transfer.result['abort_status'] = abort_result['abort_status']
                transfer.result['abort_tx_hash'] = abort_result['abort_tx_hash']
                if 'abort_error_code' in abort_result:
                    transfer.result['abort_error_code'] = abort_result['abort_error_code']
                    transfer.result['abort_message'] = abort_result['abort_message']
                # update records
                self.results_abort.append(transfer.result)
        self.results_aborting = [transfer for transfer in self.results_aborting if transfer.status == TransferStatus.CONFIRMING]
        

    def cleanup(self):
        """Cleanup the FINALIZED transfers from Interledger transfer arrays 
        """
        self.transfers = [transfer for transfer in self.transfers if transfer.status != TransferStatus.FINALIZED]


    def _filterOut(self, _list, _state: TransferStatus):
        """Cleanup elements with a particular state from an input list 
        """
        return [t for t in _list if t.state is not _state]
