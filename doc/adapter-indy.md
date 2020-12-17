# Interledger support for Hyperledger Indy

The Interledger component supports interactions with Hyperledger Indy only in the *Initiator* role to observe chages related to the configured DID.

## Interfaces

No interfaces are required for the Hyperledger Indy ledger, as the transfer triggering does not rely on events. Instead,  the Indy Initiator adapter utilises Indy functionality directly to observe the specified DID.

## Prerequisites

It is assumed that a version of [libindy](https://github.com/hyperledger/indy-sdk/blob/master/README.md#installation) is built, installed, and callable in the system path.

Beyond that, the Python SDK wrapper is required, with either `python3 setup install` or `pip install python3-indy`.

## Configurations

The configuration information of the networks is to be included in a config file that is passed to the component. The HyperLedger Indy network can be on the left side of the component as an *Initiator*.

For `type` =  `indy`, the required options are:

- **target_did**: The target DID to be observed by the Indy initiator;
- **pool_name**: The name of the Hyperledger Indy pool;
- **protocol_version**: Protocol version will be used: 1 - for Indy Node 1.3 and 2 - for Indy Node 1.4 and greater;
- **genesis_file_path**: The path to the Hyperledger Indy genesis file, instructions to create one can be found at docs to [create genesis](https://github.com/sovrin-foundation/steward-tools/tree/master/create_genesis).
- **wallet_id**: Identifier of the wallet;
- **wallet_key**: Key or passphrase used for wallet key derivation.

Example of the related sections in an Interledger configuration file *config-file-name.cfg*:

```
[service]
direction=left-to-right
left=left
right=...

[left]
type=indy
target_did=0xtargetdid
pool_name=pool
protocol_version=2
genesis_file_path=<path-to-genesis-file>
wallet_id=wallet
wallet_key=wallet_key

...
```

## Usage

### Network set up

A running Hyperledger Indy network is required before connecting with the Indy initiator according to the configurations as described in the above section.

For easy set up and testing purposes, a local Indy pool can be set up with Docker using the following commands.

```
docker build -f indy/indy-pool.dockerfile -t indy_pool .
docker run -itd -p 9701-9708:9701-9708 indy_pool
```

Any existing or customized Hyperledger Indy network should work as well in the same manner of configurations.

### Trigger by DID change

To separately validate the Indy initiator is working is as expected, with the testing set up, the following unit test can be run.

```
python -m pytest --capture=sys tests/indy/test_indyinitiator.py
```

This verifies that the configured Indy initiator is properly connected to the testing Indy pool, and could catch the transaction that is updating information related to a certain DID as specified in the configuration file.
