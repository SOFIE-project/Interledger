import asyncio
import concurrent.futures
from enum import Enum
from uuid import uuid4

from .interfaces import Initiator, Responder, ErrorCode, LedgerType


class State(Enum):
    """State of a data transfer during the protocol
    """
    READY = 1
    SENT = 2
    RESPONDED = 3
    CONFIRMING = 4
    FINALIZED = 5


class Transfer(object):
    """The information paired to a data transfer: its 'future' async call to accept(); the 'result' of the accept();
    the transfer 'state'; the event transfer 'data'.
    """
    def __init__(self):
        self.send_task = None
        self.result = None
        self.confirm_task = None
        self.state = State.READY
        self.payload = None # transactional data bundle


class Interledger(object):
    """
    Class definition of an interledger component, which is composed by an Initiator and a Responder to implement the data transfer operation.
    """
    def __init__(self, initiator: Initiator, responder: Responder):
        """Constructor
        :param object initiator: The Initiator object
        :param object responder: The Responder object
        """
        # initiator and responder
        self.initiator = initiator
        self.responder = responder

        # transfer ralated
        self.transfers = []

        self.transfers_sent = []
        self.transfers_responded = []

        self.results_committing = []
        self.results_commit = []

        self.results_aborting = []
        self.results_abort = []
        
        self.up = False
        
    async def run(self):
        """Run the interledger.
        Wait for new transfers from the Initiator, forward them to the Responder and finalize the protocol with the Intiator.
        """
        self.up = True
        while self.up:

            # Triggers
            receive = asyncio.ensure_future(self.receive_transfer())
            if not self.transfers_sent and not self.results_committing and not self.results_aborting:
                await receive
            else:
                result = asyncio.ensure_future(self.transfer_result())
                confirm = asyncio.ensure_future(self.confirm_transfer())
                asyncio.wait([receive, result, confirm], return_when=asyncio.FIRST_COMPLETED)

            # Actions
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

    # Action
    async def send_transfer(self):
        """Forward the stored transfers to the Responder.
        """
        for transfer in self.transfers:
            if transfer.state == State.READY:
                transfer.state = State.SENT
                
                print("********** send transfer ************")
                print(f"{transfer.payload}")
                print("*************************************")
                
                # generate nonce
                nonce, data = transfer.payload['nonce'], transfer.payload['data']
                # send data to destination ledger
                transfer.send_task = asyncio.ensure_future(self.responder.send_data(nonce, data))
                self.transfers_sent.append(transfer)

    # Trigger
    async def transfer_result(self):
        """Store the results of the transfers sent to the Responder. 
           This operation blocks until at least one future has been completed.
        """
        send_tasks = [transfer.send_task for transfer in self.transfers_sent]
        if not send_tasks:
            return
        await asyncio.wait(send_tasks, return_when=asyncio.FIRST_COMPLETED)
        for transfer in self.transfers_sent:
            if transfer.state == State.SENT and transfer.send_task.done():
                transfer.result = transfer.send_task.result()
                transfer.state = State.RESPONDED
                self.transfers_responded.append(transfer)
        # update records
        self.transfers_sent = [transfer for transfer in self.transfers_sent if transfer.state ==State.SENT]

    # Action
    async def process_result(self):
        """Process the result of the responder: trigger the commit() or the abort()
           operation of the Initiator to confirm the status of the transfer.
        """
        for transfer in self.transfers_responded:
            if transfer.state == State.RESPONDED:
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

                transfer.state = State.CONFIRMING
        self.transfers_responded = [transfer for transfer in self.transfers_responded if transfer.state == State.RESPONDED]

    async def confirm_transfer(self):
        """Confirm the status of transfer as either commit or abort based on the initiator operations, to complete the protocol
        """
        confirm_tasks = [transfer.confirm_task for transfer in self.results_committing + self.results_aborting]
        if not confirm_tasks:
            return
        await asyncio.wait(confirm_tasks, return_when=asyncio.FIRST_COMPLETED)

        for transfer in self.results_committing:
            if transfer.state == State.CONFIRMING and transfer.confirm_task.done():
                # retrieve confirm result and update state
                commit_result = transfer.confirm_task.result()
                transfer.state = State.FINALIZED
                # record confirm result
                transfer.result['commit_status'] = commit_result['commit_status']
                transfer.result['commit_tx_hash'] = commit_result['commit_tx_hash']
                if 'commit_error_code' in commit_result:
                    transfer.result['commit_error_code'] = commit_result['commit_error_code']
                    transfer.result['commit_message'] = commit_result['commit_message']
                # update records
                self.results_commit.append(transfer.result)
        self.results_committing = [transfer for transfer in self.results_committing if transfer.state == State.CONFIRMING]

        for transfer in self.results_aborting:
            if transfer.state == State.CONFIRMING and transfer.confirm_task.done():
                # retrieve confirm result and update state
                abort_result = transfer.confirm_task.result()
                transfer.state = State.FINALIZED
                # record abort result
                transfer.result['abort_status'] = abort_result['abort_status']
                transfer.result['abort_tx_hash'] = abort_result['abort_tx_hash']
                if 'abort_error_code' in abort_result:
                    transfer.result['abort_error_code'] = abort_result['abort_error_code']
                    transfer.result['abort_message'] = abort_result['abort_message']
                # update records
                self.results_abort.append(transfer.result)
        self.results_aborting = [transfer for transfer in self.results_aborting if transfer.state == State.CONFIRMING]
        

    def cleanup(self):
        """Cleanup the FINALIZED transfers from Interledger transfer arrays 
        """
        self.transfers = [transfer for transfer in self.transfers if transfer.state != State.FINALIZED]


    def _filterOut(self, _list, _state: State):
        """Cleanup elements with a particular state from an input list 
        """
        return [t for t in _list if t.state is not _state]
