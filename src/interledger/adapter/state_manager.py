import asyncio
import json
from copy import deepcopy
from pathlib import Path
from hfc.fabric import Client


from .interfaces import ILStateManager
from ..transfer import TransferStatus, Transfer


class LocalILStateManger(ILStateManager):
    def __init__(self) -> None:
        # this is to be used in compatible single node mode and for DIL verification purpose
        self.local_transfers = {}  # local state layer in memory, {id: transfer}
        self.transfers_ready = []
        self.transfers_responded = []

    async def create_entry(self,
                           id: str,
                           transfer: Transfer) -> bool:
        if id in self.local_transfers:
            return False
        self.local_transfers[id] = deepcopy(transfer)
        return True

    async def signal_send_acceptance(self,
                                     id: str) -> bool:
        if id not in self.local_transfers:
            raise KeyError
        t = self.local_transfers[id]
        if t.send_accepted:
            return False  # rejected
        t.send_accepted = True
        return True

    async def signal_confirm_acceptance(self,
                                        id: str) -> bool:
        if id not in self.local_transfers:
            raise KeyError
        t = self.local_transfers[id]
        if t.confirm_accepted:
            return False  # rejected
        t.confirm_accepted = True
        t_responded = deepcopy(t)
        self.transfers_responded.append(t_responded)
        return True

    async def update_entry(self,
                           id: str,
                           status: TransferStatus,
                           transfer: Transfer = None) -> bool:
        if id not in self.local_transfers:
            raise KeyError
        t = self.local_transfers[id]
        if transfer:
            t.send_accepted = transfer.send_accepted
            t.confirm_accepted = transfer.confirm_accepted
            t.result = transfer.result

        t.status = status
        return True

    async def receive_entry_events(self,
                                   status: TransferStatus) -> None:
        if status not in (TransferStatus.READY, TransferStatus.RESPONDED):
            raise ValueError
        entries = [t for t in self.local_transfers.values()
                   if t.status == status]
        if status == TransferStatus.READY:
            self.transfers_ready.extend(entries)
        elif status == TransferStatus.RESPONDED:
            self.transfers_responded.extend(entries)
        else:
            raise ValueError


class FabricILStateManager(LocalILStateManger):
    def __init__(self,
                 net_profile: Path,
                 channel_name: str,
                 cc_name: str,
                 cc_version: str,
                 org_name: str,
                 user_name: str,
                 peer_name: str) -> None:

        self.entries_ready = [] # to store list of json objects
        self.entries_responded = [] # to store list of json objects

        self.client = Client(net_profile=net_profile)
        if not self.client:
            raise ValueError("Invalid network profile.")

        self.channel_name = channel_name
        self.channel = self.client.new_channel(channel_name)
        print(f'HF state manager - channel: {self.channel}')

        self.cc_name = cc_name
        self.cc_version = cc_version

        self.user = self.client.get_user(org_name, user_name)
        print(f'HF state manager - orgs: {self.client.organizations}')
        print(self.client.organizations['Org1MSP']._users)
        print(f'HF state manager - user: {self.user}')

        self.peers = [self.client.get_peer(peer_name)]
        print(f'HF state manager - peers: {self.peers}')

        self.hub = None
        self.reg_num = None
        self.events = []

    async def get_height(self):
        info = await self.client.query_info(self.user, self.channel_name, self.peers)
        return info.height

    async def create_entry(self,
                           id: str,
                           transfer: Transfer) -> bool:

        payload = transfer.payload
        nonce, data = payload.nonce, payload.data

        try:
            await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                cc_version=self.cc_version,
                fcn="createTransferEntry",
                args=[nonce, data],
                wait_for_event=True)
            return True

        except Exception as e:
            print(e)
            return False

    async def signal_send_acceptance(self,
                                     id: str,
                                     signal_acceptance: bool = True) -> bool:
        try:
            await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                cc_version=self.cc_version,
                fcn="updateTransferEntry",
                args=[id, TransferStatus.READY, signal_acceptance])
            return True

        except Exception as e:
            print(e)
            return False

    async def update_entry(self,
                           id: str,
                           status: TransferStatus,
                           transfer: Transfer = None) -> bool:

        signal_acceptance, result = transfer.send_accepted, transfer.result

        try:
            await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                cc_version=self.cc_version,
                fcn="updateTransferEntry",
                args=[id, status, signal_acceptance, result])
            return True

        except Exception as e:
            print(e)
            return False

    async def receive_entry_events(self,
                                   event: TransferStatus) -> None:

        self.hub = self.channel.newChannelEventHub(self.peers[0], self.user)
        self.reg_num = self.hub.registerBlockEvent(
            onEvent=self._event_handler)

        if not self.height:
            self.height = await self.get_height()

        stream = self.hub.connect(filtered=False, start=self.height)
        try:
            await asyncio.wait_for(stream, timeout=1)
        except asyncio.TimeoutError:
            pass

        self.height = await self.get_height()

        if event == TransferStatus.READY:
            self.transfers_ready = self._buffer_data(self.entries_ready)
        if event == TransferStatus.RESPONDED:
            self.transfers_responded = self._buffer_data(self.entries_responded)

        # clean up
        self.hub.disconnect()
        self.hub.unregisterBlockEvent(self.reg_num)

    def _event_handler(self, event_obj):
        d = event_obj['data']['data']
        actions = d[0]['payload']['data']['actions']
        action = actions[0]

        event = action['payload']['action']['proposal_response_payload']['extension']['events']
        event_name = event['event_name']

        if event_name == "transferReady":
            self.entries_ready.append(event)
        if event_name == "transferResponded":
            self.entries_responded.append(event)


    def _buffer_data(self, events):

        res = []
        for event in events:
            transfer = Transfer()

            json_str = event['payload']
            t_obj = json.loads(json_str)
            
            transfer.status, = t_obj['status']
            transfer.payload = t_obj['payload']

            if transfer.status == TransferStatus.RESPONDED:
                transfer.send_accepted = t_obj['sendAcceptance']
                transfer.result = json.loads(t_obj['result'])   

            res.append(transfer)

        return res
