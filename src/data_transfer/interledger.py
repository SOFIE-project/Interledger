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
    FINALIZED = 4


class Transfer(object):
    """The information paired to a data transfer: its 'future' async call to accept(); the 'result' of the accept();
    the transfer 'state'; the event transfer 'data'.
    """
    def __init__(self):
        self.future = None
        self.result = None
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
        self.pending = 0
        self.transfers = []
        self.transfers_sent = []
        self.results_abort = []
        self.results_commit = []
        # switch on / off
        self.keep_running = True
        
    async def run(self):
        """Run the interledger.
        Wait for new transfers from the Initiator, forward them to the Responder and finalize the protocol with the Intiator.
        """
        while self.keep_running:
            # Triggers
            receive = asyncio.ensure_future(self.receive_transfer())
            print("pending: ", self.pending)
            if not self.pending:
                await receive
            else:
                result = asyncio.ensure_future(self.transfer_result())
                await asyncio.wait([receive, result], return_when=asyncio.FIRST_COMPLETED)
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
        self.keep_running = False

    # Trigger
    async def receive_transfer(self):
        """Receive the list of transfers from the Initiator. This operation blocks until it receives at least one transfer.
        """
        print("receive_transfer")
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
        print("send_tansfer")
        for transfer in self.transfers:
            if transfer.state == State.READY:
                transfer.state = State.SENT
                # generate nonce
                nonce, data = transfer.payload['nonce'], transfer.payload['data']
                # send data to destination ledger
                transfer.future = asyncio.ensure_future(self.responder.send_data(nonce, data))
                self.transfers_sent.append(transfer)
                self.pending += 1

    # Trigger
    async def transfer_result(self):
        """Store the results of the transfers sent to the Responder. This operation blocks until at least one future has been completed.
        """
        print("transfer_result")
        futures = [transfer.future for transfer in self.transfers_sent]
        await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)
        for transfer in self.transfers_sent:
            if transfer.state == State.SENT and transfer.future.done():
                transfer.result = transfer.future.result()
                transfer.state = State.RESPONDED

    # Action
    async def process_result(self):
        """Process the result of the responder: trigger the commit() or the abort() operation of the Initiator to complete the protocol.
        """
        print("process_result")
        for transfer in self.transfers_sent:
            if transfer.state == State.RESPONDED:
                id = transfer.payload['id']
                print(transfer.result)
                if transfer.result["status"]:
                    # If the Responder ledger is KSI, pass the KSI id (stored in 
                    # tx_hash field of transfer) to the Initiator's commit function
                    if self.responder.ledger_type == LedgerType.KSI:
                        asyncio.ensure_future(self.initiator.commit_sending(id, transfer.result['tx_hash'].encode()))
                    else:
                        asyncio.ensure_future(self.initiator.commit_sending(id))
                    # TODO check whether commit was successful
                    # check return value
                    self.results_commit.append(transfer.result)
                else:
                    # TODO check error code of the accept transaction:
                    asyncio.ensure_future(self.initiator.abort_sending(id, ErrorCode.TRANSACTION_FAILURE))
                    # TODO check whether abort was successful
                    # check return value
                    self.results_abort.append(transfer.result)
                transfer.state = State.FINALIZED
                self.pending -= 1

    def cleanup(self):
        """Cleanup the FINALIZED transfers from Interledger transfer arrays 
        """
        print("cleanup")
        transfers_unfinalized = self._filterOut(self.transfers, State.FINALIZED)
        self.transfers.clear()
        self.transfers = transfers_unfinalized

        transfers_sent_unfinalized = self._filterOut(self.transfers_sent, State.FINALIZED)
        self.transfers_sent.clear()
        self.transfers_sent = transfers_sent_unfinalized

    def _filterOut(self, _list, _state: State):
        """Cleanup elements with a particular state from an input list 
        """
        return [t for t in _list if t.state is not _state]
