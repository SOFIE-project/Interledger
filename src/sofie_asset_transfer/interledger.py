from .interfaces import Initiator, Responder
import time, asyncio
from asyncio import Condition
from typing import List
import concurrent.futures
from enum import Enum


class State(Enum):
    """State of a transfer during the protocol
    """
    READY = 1
    SENT = 2
    COMPLETED = 3
    PROCESSED = 4


class Transfer(object):
    """The information paired to a data transfer: its 'future' async call to accept(); the 'result' of the accept();
    the transfer 'state'; the event transfer 'data'.
    """

    def __init__(self):
        self.future = None
        self.result = None
        self.state = State.READY
        self.data = None        # transactional data bundle


class Interledger(object):
    """
    Class implementing the interledger component. The component is composed by an Initiator and a Responder to implement the asset transfer operation.
    """

    def __init__(self, initiator: Initiator, responder: Responder):
        """
        :param object initiator: The Initiator object
        :param object responder: The Responder object
        """
        self.initiator = initiator
        self.responder = responder
        self.transfers = []
        self.transfers_sent = []
        self.pending = 0
        self.keep_running = True
        
        # Debug
        self.results_abort = []
        self.results_commit = []


    def stop(self):
        """Stop the interledger run() operation
        """
        self.keep_running = False

        
    # blocking, trigger
    async def receive_transfer(self):
        """Receive the list of transfers from the Initiator. This operation blocks until it receives at least one transfer.
        """
        transfers = await self.initiator.get_transfers()
        if len(transfers) > 0:
            self.transfers.extend(transfers)

        return len(transfers)

 
    # non blocking, action
    async def send_transfer(self):
        """Forward the stored transfers to the Responder.
        """

        for t in self.transfers:
            if t.state == State.READY:
                t.state = State.SENT
                t.future = asyncio.ensure_future(self.responder.receive_transfer(t))
                self.transfers_sent.append(t)
                self.pending += 1

    
    # blocking, trigger
    async def transfer_result(self):
        """Store the results of the transfers sent to the Responder. This operation blocks until at least one transfer has been completed.
        """

        futures = [t.future for t in self.transfers_sent]
        await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)

        for t in self.transfers_sent:
            if t.state == State.SENT and not t.state == State.COMPLETED and t.future.done():
                t.result = t.future.result()
                t.state = State.COMPLETED


    # non blocking: action
    async def process_result(self):
        """Process the result of the responder: trigger the commit() or the abort() operation of the Initiator to complete the protocol.
        """

        for t in self.transfers_sent:

            if t.state == State.COMPLETED:
                
                if t.result:
                    asyncio.ensure_future(self.initiator.commit_transfer(t))
                    self.results_commit.append(t.result)
                else:
                    asyncio.ensure_future(self.initiator.abort_transfer(t))
                    self.results_abort.append(t.result)

                t.state = State.PROCESSED
                self.pending -= 1


    async def run(self):
        """Run the interledger. Wait for transfers from the Initiator, forward them to the Responder and finalize the protocol with the Intiator.
        """
 
        while self.keep_running:

            receive = asyncio.ensure_future(self.receive_transfer())

            if not self.pending:
                await receive
            else:
                result = asyncio.ensure_future(self.transfer_result())
                await asyncio.wait([receive, result], return_when=asyncio.FIRST_COMPLETED)

            send = asyncio.ensure_future(self.send_transfer())
            process = asyncio.ensure_future(self.process_result())

            await send
            await process


        # TODO Add some closing procedure
