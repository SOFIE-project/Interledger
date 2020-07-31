import time, asyncio
import ast
from hfc.fabric import Client

from .interfaces import Initiator, Responder, ErrorCode
from .interledger import Transfer


class FabricInitializer:
    """This provides the proper fabric client wrapper
    """
    def __init__(self, net_profile=None, channel_name=None, cc_name=None, cc_version=None, org_name=None, user_name=None, peer_name=None):
        self.client = Client(net_profile=net_profile)
        assert self.client
        print("---client---")
        print(self.client.orderers)
        print(self.client.peers)
        print("---client---")

        self.channel_name = channel_name
        self.channel = self.client.new_channel(channel_name)
        print("---channel---")
        print("client channels: ", self.client._channels)
        print("channel: ", self.client.get_channel(channel_name))
        print("channel name: ", self.client.get_channel(channel_name).name)
        print("channel peers: ", self.client.get_channel(channel_name).peers)
        print("channel orderers: ", self.client.get_channel(channel_name).orderers)
        print("---channel---")
        assert self.channel

        self.cc_name = cc_name
        self.cc_version = cc_version

        self.user = self.client.get_user(org_name, user_name)
        assert self.user

        self.peers = [self.client.get_peer(peer_name)]
        assert self.peers
        print("---parameters---")
        print("User: ", self.user)
        print("Peers: ", self.peers)
        print("cc name:", self.cc_name)
        print("---parameters---")

        self.hub = None
        self.reg_nub = None

    async def get_height(self):
        info = await self.client.query_info(self.user, self.channel_name, self.peers)
        return info.height


class FabricInitiator(FabricInitializer, Initiator):
    """Fabric implementation of the Initiator.
    """
    def __init__(self, net_profile=None, channel_name=None, cc_name=None, cc_version=None, org_name=None, user_name=None, peer_name=None):
        FabricInitializer.__init__(
            self,
            net_profile=net_profile, 
            channel_name=channel_name, 
            cc_name=cc_name, 
            cc_version=cc_version, 
            org_name=org_name, 
            user_name=user_name, 
            peer_name=peer_name
        )

        self.height = None
        self.entries = []

    async def listen_for_events(self) -> list:
        """Listen for events fired by the Initiator injected chaincode stored in the connected HyperLedger Fabric network.

        :returns: The event transfer lists
        :rtype: list
        """
        transfers = [] # initialize transfer list

        self.hub = self.channel.newChannelEventHub(self.peers[0], self.user)
        self.reg_num = self.hub.registerBlockEvent(
            onEvent=self.event_handler)
        # print(f"reg_num: {self.reg_num}")

        # wait for some time
        # print("Start listening...")
        if not self.height:
            self.height = await self.get_height()
        # start = await self.get_height()
        # await asyncio.sleep(12)
        # stop = await self.get_height()

        # start listening and store the events
        # print(f"Start listening from : {self.height}")
        # print(f"Debug@Hub peer: {self.hub._peer} \nof type {type(self.peers[0])}")
        stream = self.hub.connect(filtered=False, start=self.height)
        try:
            await asyncio.wait_for(stream, timeout=1)
        except asyncio.TimeoutError:
            # print('timeout!')
            pass

        self.height = await self.get_height()

        # check the events
        if self.entries:
            transfers = self._buffer_data(self.entries)
            print("cached transfers:", len(transfers))
            
        # clean up
        # print(self.hub._reg_nums)
        self.hub.disconnect()
        # print(self.hub._reg_nums)
        # self.hub.unregisterBlockEvent(self.reg_num)
        # print(self.hub._reg_nums)
        self.entries.clear()
        
        return transfers
            

    async def commit_sending(self, id: str) -> dict:
        """Initiate the commit operation to the connected HyperLedger Fabric network.

        :param str id: the identifier in the originating ledger for a data item
        :rtype: dict {
            'commit_status': bool,
            'commit_tx_hash': str,
            'exception': object,# only with errors
            'commit_error_code': Enum, # only with errors
            'commit_message': str      # only with errors
        }
        """
        # invoke interledgerCommit
        try:
            result = await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                fcn="InterledgerCommit",
                args=[id],
                wait_for_event=True)
            # print("commit result:", result)
            return {"commit_status": True,
                    "commit_tx_hash": "0xfake_tx_hash"} 
        except Exception as err:
            # print(err)
            return {"commit_status": False, 
                    "commit_error_code": ErrorCode.TRANSACTION_FAILURE,
                    "commit_message": "Error in the transaction",
                    "commit_tx_hash": "0xfake_tx_hash"}

    async def abort_sending(self, id: str, reason: int):
        """Initiate the abort operation to the connected HyperLedger Fabric.

        :param str id: the identifier in the originating ledger for a data item
        :param int reason: the code to signal the predefined reasons 
        :rtype: dict {
            'abort_status': bool,
            'abort_tx_hash': str,
            'exception': object,# only with errors
            'abort_error_code': Enum, # only with errors
            'abort_message': str      # only with errors
        }
        """

        # invoke interledgerAbort
        try:
            result = await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                fcn="interledgerAbort",
                args=[int(id), int(reason)],
                wait_for_event=True)
            # print("abort result:", result)
            return {"abort_status": True,
                    "abort_tx_hash": "0xfake_tx_hash"}
        except:
            return {"abort_status": False, 
                    "abort_error_code": ErrorCode.TRANSACTION_FAILURE,
                    "abort_message": "Error in the transaction",
                    "abort_tx_hash": "0xfake_tx_hash"}

    def event_handler(self, event_obj):
        print(f"block event handler triggered....")

        d = event_obj['data']['data']
        actions = d[0]['payload']['data']['actions']
        action = actions[0]
        print(f"action payload: {action['payload']}")
        event = action['payload']['action']['proposal_response_payload']['extension']['events']
        event_name = event['event_name']
        print(f"Event name: {event_name}")

        if event_name == "InterledgerEventSending":
            self.entries.append(event)

    def _buffer_data(self, events):
        res = []
        for event in events:
            print(f"event to be cached: {event}")
            transfer = Transfer()
            byte_str = event['payload']

            # encode the byte string and decode into a dict
            dict_str = byte_str.decode("UTF-8")
            parsed = ast.literal_eval(dict_str)
            transfer.payload = {'id': parsed['Id'], 'data': parsed['Data']}
            print("*********** buffer data *************")
            print(f"{transfer.payload}")
            print("*************************************")
            
            res.append(transfer)
        return res

class FabricResponder(FabricInitializer, Responder):
    def __init__(self, net_profile=None, channel_name=None, cc_name=None, cc_version=None, org_name=None, user_name=None, peer_name=None):
        FabricInitializer.__init__(
            self,
            net_profile=net_profile, 
            channel_name=channel_name, 
            cc_name=cc_name, 
            cc_version=cc_version, 
            org_name=org_name, 
            user_name=user_name, 
            peer_name=peer_name
        )

    async def send_data(self, nonce: str, data: bytes):
        # invoke interledgerReceive
        try: 
            result = await self.client.chaincode_invoke(
                requestor=self.user,
                peers=self.peers,
                channel_name=self.channel_name,
                cc_name=self.cc_name,
                cc_version=str(self.cc_version),
                fcn="interledgerReceive",
                args=[nonce, data],
                wait_for_event=True)
            # print("send data result:", result)
            return {"status": True,
                    "tx_hash": "0xfake_tx_hash"}
        except Exception as e:
            return {"status": False, 
                    "error_code": ErrorCode.TRANSACTION_FAILURE,
                    "message": "Error in the transaction",
                    "tx_hash": "0xfake_tx_hash",
                    "exception": e}