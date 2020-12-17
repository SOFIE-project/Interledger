from typing import List

from interledger.adapter.interfaces import LedgerType, Initiator, Responder, MultiResponder


class MockInitiator(Initiator):

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

class MockResponder(Responder):

    def __init__(self):
        self.events = []
        self.ledger_type = LedgerType.ETHEREUM

    async def send_data(self, nonce: str, data: bytes):

        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}


# Responder which getting negative result

class MockResponderAbort(Responder):

    async def send_data(self, nonce: str, data: bytes):
        return {"status": False, "tx_hash": "0xfail_tx_hash"}


class MockMultiResponder(MultiResponder):
    async def send_data_inquire(self, nonce: str, data: bytes):
        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}

    async def send_data(self, nonce: str, data: bytes):
        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}

    async def abort_send_data(self, nonce: str, reason: int):
        return {"status": False, "tx_hash": "0xfail_tx_hash"}


class MockMultiResponderAbort(MultiResponder):
    async def send_data_inquire(self, nonce: str, data: bytes):
        return {"status": False, "tx_hash": "0xfail_tx_hash"}

    async def send_data(self, nonce: str, data: bytes):
        return {"status": True, "tx_hash": "0xsuccess_tx_hash"}

    async def abort_send_data(self, nonce: str, reason: int):
        return {"status": False, "tx_hash": "0xfail_tx_hash"}
