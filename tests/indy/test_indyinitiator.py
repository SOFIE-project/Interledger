import pytest
import json
import pprint
from indy import pool, ledger, wallet, did

from interledger.adapter.interfaces import ErrorCode
from interledger.transfer import Transfer
from interledger.adapter.indy import IndyInitiator, print_log
from .utils import setup_indy, get_pool_genesis_txn_path


# temp config for testing if not provided
GENESIS_FILE_PATH = get_pool_genesis_txn_path('pool')


# Test the Indy initiator - Constructor
def test_init(config):
    # set up indy initiator
    target_did, pool_name, protocol_version, genesis_file_path, wallet_id, wallet_key = setup_indy(config)
    genesis_file_path = genesis_file_path or GENESIS_FILE_PATH

    # print(f'parsed info about Indy: {target_did, pool_name, protocol_version, genesis_file_path, wallet_id, wallet_key}')
    init = IndyInitiator(target_did, pool_name, protocol_version, genesis_file_path, wallet_id, wallet_key)

    # validate fields of initiator
    assert init

    assert init.pool_name == pool_name
    assert init.protocol_version == protocol_version
    assert type(init.pool_config) == str
    assert "genesis_txn" in init.pool_config
    assert type(init.wallet_config) == str
    assert "id" in init.wallet_config
    assert type(init.wallet_credentials) == str
    assert "key" in init.wallet_credentials

    assert not init.pool_handle
    assert not init.wallet_handle
    assert not init.client_did
    assert not init.client_verkey
    assert not init.verkey

    assert not init.ready
    assert isinstance(init.entries, list)
    assert not init.entries


# Test get_transfers
@pytest.mark.asyncio
async def test_initiator_listen_for_events(config):
    # set up indy initiator
    target_did, pool_name, protocol_version, genesis_file_path, wallet_id, wallet_key = setup_indy(config)
    genesis_file_path = genesis_file_path or GENESIS_FILE_PATH

    init = IndyInitiator(target_did, pool_name, protocol_version, genesis_file_path, wallet_id, wallet_key)

    # validate fields of initiator
    assert init

    # check status before creating handlers
    assert not init.pool_handle
    assert not init.wallet_handle
    assert not init.client_did
    assert not init.client_verkey
    assert not init.verkey

    assert not init.ready
    assert isinstance(init.entries, list)
    assert not init.entries

    # create handlers
    res = await init.create_handlers()
    assert res

    # check status afterwards
    assert init.pool_handle
    assert init.wallet_handle
    print(f'wallet handle: {init.wallet_handle}')
    assert init.client_did
    assert init.client_verkey
    

    assert init.ready
    assert isinstance(init.entries, list)
    assert not init.verkey # should remain none
    assert not init.entries # should remain empty

    # generate and store steward DID and verkey
    steward_seed = '000000000000000000000000Steward1'
    did_json = json.dumps({'seed': steward_seed})
    steward_did, steward_verkey = await did.create_and_store_my_did(init.wallet_handle, did_json)
    print_log('Steward DID: ', steward_did)
    print_log('Steward Verkey: ', steward_verkey)

    # Generating and storing trust anchor DID and verkey
    trust_anchor_did, trust_anchor_verkey = await did.create_and_store_my_did(init.wallet_handle, "{}")
    print_log('Trust anchor DID: ', trust_anchor_did)
    print_log('Trust anchor Verkey: ', trust_anchor_verkey)

    # replace the initiator target DID, for testing convenience
    # in production, this will not be updated manually like this
    init.target_did = trust_anchor_did

    # building NYM request to add Trust Anchor to the ledger
    nym_transaction_request = await ledger.build_nym_request(submitter_did=steward_did,
                                                             target_did=trust_anchor_did,
                                                             ver_key=trust_anchor_verkey,
                                                             alias=None,
                                                             role='TRUST_ANCHOR')
    print_log('NYM transaction request: ')
    pprint.pprint(json.loads(nym_transaction_request))

    # sending NYM request to the ledger\n')
    nym_transaction_response = await ledger.sign_and_submit_request(pool_handle=init.pool_handle,
                                                                    wallet_handle=init.wallet_handle,
                                                                    submitter_did=steward_did,
                                                                    request_json=nym_transaction_request)
    print_log('NYM transaction response: ')
    pprint.pprint(json.loads(nym_transaction_response))

    transfers = await init.listen_for_events()

    assert transfers
    assert len(transfers) == 1
    print(transfers[0])

    # update new verkey to ledger and check listening
    new_verkey = await did.replace_keys_start(init.wallet_handle, trust_anchor_did, "{}")
    print_log('New Trust Anchor Verkey: ', new_verkey)

    nym_request = await ledger.build_nym_request(trust_anchor_did, trust_anchor_did, new_verkey, None, 'TRUST_ANCHOR')
    print_log('NYM request:')
    pprint.pprint(json.loads(nym_request))

    nym_response = await ledger.sign_and_submit_request(init.pool_handle, init.wallet_handle, trust_anchor_did, nym_request)
    print_log('NYM response:')
    pprint.pprint(json.loads(nym_response))

    transfers = await init.listen_for_events()

    assert transfers
    assert len(transfers) == 1
    print(transfers[0])


#
# Test abort_transfer
#

@pytest.mark.asyncio
async def test_initiator_abort(config):
    pass


#
# Test commit_transfer
#

@pytest.mark.asyncio
async def test_initiator_commit(config):
    pass


@pytest.mark.asyncio
async def test_initiator_commit_transaction_failure(config):
    pass
