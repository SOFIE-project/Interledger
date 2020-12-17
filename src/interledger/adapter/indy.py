import json
import pprint

from indy import pool, ledger, wallet, did
from indy.error import IndyError

from .interfaces import Initiator
from ..transfer import Transfer


def print_log(value_color="", value_noncolor=""):
    """set the colors for text."""
    HEADER = '\033[92m'
    ENDC = '\033[0m'
    print(HEADER + value_color + ENDC + str(value_noncolor))


class IndyInitializer:
    """This provides the proper Hyperledger Indy client wrapper
    """
    def __init__(self, pool_name, protocol_version, genesis_file_path, \
        wallet_id, wallet_key):

        self.ready = False # intial status is False before all handlers are ready

        self.pool_name = pool_name
        self.protocol_version = protocol_version
        self.pool_config = json.dumps({'genesis_txn': str(genesis_file_path)})
        self.wallet_config = json.dumps({"id": wallet_id})
        self.wallet_credentials = json.dumps({"key": wallet_key})

        self.pool_handle = None
        self.wallet_handle = None
        self.client_did = None
        self.client_verkey = None


    async def create_handlers(self) -> bool:
        try:
            await pool.set_protocol_version(self.protocol_version)

            print_log('Creates a new local pool ledger configuration that is used '
                    'later when connecting to ledger.\n')
            
            try:
                await pool.create_pool_ledger_config(config_name=self.pool_name, config=self.pool_config)
            except IndyError:
                await pool.delete_pool_ledger_config(config_name=self.pool_name)
                await pool.create_pool_ledger_config(config_name=self.pool_name, config=self.pool_config)

            print_log('\nOpen pool ledger and get handle from libindy\n')
            self.pool_handle = await pool.open_pool_ledger(config_name=self.pool_name, config=None)

            print_log('\nCreating new secure wallet\n')
            try:
                await wallet.create_wallet(self.wallet_config, self.wallet_credentials)
            except IndyError:
                await wallet.delete_wallet(self.wallet_config, self.wallet_credentials)
                await wallet.create_wallet(self.wallet_config, self.wallet_credentials)

            print_log('\nOpen wallet and get handle from libindy\n')
            self.wallet_handle = await wallet.open_wallet(self.wallet_config, self.wallet_credentials)

            print_log('\nGenerating and storing DID and verkey representing a Client '
                    'that wants to obtain Trust Anchor Verkey\n')
            self.client_did, self.client_verkey = await did.create_and_store_my_did(self.wallet_handle, "{}")
            print_log('Client DID: ', self.client_did)
            print_log('Client Verkey: ', self.client_verkey)
            self.ready = True

        except IndyError as e:
            print('Error occurred: %s' % e)
            self.ready = False
        
        return self.ready


class IndyInitiator(IndyInitializer, Initiator):
    """Indy implementation of the Initiator.
    """
    def __init__(self, target_did, pool_name, protocol_version, genesis_file_path, \
        wallet_id, wallet_key):

        IndyInitializer.__init__(self, pool_name, protocol_version, genesis_file_path, \
            wallet_id, wallet_key)

        self.target_did = target_did
        self.verkey = None
        self.entries = []


    async def listen_for_events(self) -> list:
        """Listen for entries of changes on the Hyperledger Indy ledger and generate transfers accordingly.

        :returns: The event transfer lists
        :rtype: list
        """
        if not self.ready:
            res = await IndyInitializer.create_handlers()
            if not res: exit(1)

        # get entries from GET_NYM responses
        get_nym_request = await ledger.build_get_nym_request(submitter_did=self.client_did,
                                                             target_did=self.target_did)

        get_nym_response_json = await ledger.submit_request(pool_handle=self.pool_handle,
                                                            request_json=get_nym_request)
        
        get_nym_response = json.loads(get_nym_response_json)
        print_log('GET_NYM response: ')
        pprint.pprint(get_nym_response)

        # check verkey
        verkey_from_ledger = json.loads(get_nym_response['result']['data'])['verkey']
        if verkey_from_ledger != self.verkey:
            self.verkey = verkey_from_ledger
            self.entries = [(verkey_from_ledger, get_nym_response)]
        else:
            self.entries = []
        
        # convert to transfers and return
        return self._buffer_data(self.entries)


    # Helper function
    def _buffer_data(self, entries: list):
        """Helper function to create a list of Transfer object from a list of indy entries of event
        """
        transfers = []
        for entry in entries:
            transfer = Transfer()
            transfer.payload = {'id': entry[0], 'data': entry[1]} # id will be string inside interledger
            transfers.append(transfer)
            print("*********** buffer data *************")
            print(f"{transfer.payload}")
            print("*************************************")
        return transfers

    
    async def commit_sending(self, id: str) -> dict:
        """Initiate the commit operation to the connected HyperLedger Indy network.

        :param str id: the identifier in the originating ledger for a data item
        :rtype: dict {
            'commit_status': bool,
            'commit_tx_hash': str,
            'exception': object,# only with errors
            'commit_error_code': Enum, # only with errors
            'commit_message': str      # only with errors
        }
        """
        return {"commit_status": True,
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
        return {"abort_status": True,
                "abort_tx_hash": "0xfake_tx_hash"}