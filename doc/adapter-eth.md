# Interledger support for Ethereum networks

The Interledger component surpports interaction with both private and public Ethereum networks in both the *Initiator* and *Responder* roles. 

## Interfaces for data transfer

Smart contract interfaces for data transfer are provided in `solidity/contracts` as `InterledgerSenderInterface.sol` and `InterledgerReceiverInterface.sol`.

### Sending

The data sending interface `InterledgerSenderInterface` is to be implemented by the *Initiator* smart contract.

To trigger the sending action accross ledgers, the data payload should be included in the event `InterledgerEventSending(id, data)`, where the `id` is the identifier of the data sending event, while the bytes `data` is the actual data to be sent.

Once the data has been processed by the *Responder* smart contract, the resulting status (Accept/Reject) is reported back to the *Initiator* using methods of `interledgerCommit(id)` or `interledgerAbort(id, reason)`, where `id` is the same event identifier and `reason` is the error code to indicate the cause of failure.

For cases where additional information is returned to the initiator, an override of the `interledgerCommit(id, data)` is provided, where `data` is the additional information in bytes.

### Receiving

The data receiving interface `InterledgerReceiverInterface` is to be implemented by the *Responder* smart contract.

The method `interledgerReceive(nonce, data)` is used to receive data from the interledger component to the ledger, where the `nonce` is unique identifier of the data transfer object inside the interledger component. The storage or processing logic can be added here before replying whether the incoming data payload is accepted or rejected by the application logic of the smart contract, which is indicated using the events `InterledgerEventAccepted(nonce)` or `InterledgerEventRejected(nonce)`.

## Configuration

The configuration information of the networks is to be included in a config file that is passed to the component. The Ethereum network can be on both sides of the component, so all `direction` options (`left`, `right` or `both`) are possible.

For `type` =  `ethereum`, the required options are:

- **url:** the ethereum network url (localhost or with [infura](https://infura.io/));
- **port:** if the url is localhost;
- **minter:** the contract minter (creator) address;
- **contract:** the contract address;
- **contract_abi:** path to the file describing the contract ABI in JSON format.

Example of the Interledger configuration file *config-file-name.cfg*:

```
[service]
direction=both
left=left
right=right

[left]
type=ethereum
url=http://localhost
port=7545
minter=0x167E5c43697d7Bfb86e09E346A088fB63A461B11
contract=0x820381CE97F81Fd934359425699A730FAC6C0258
contract_abi=solidity/contracts/GameToken.abi.json

[right]
type=ethereum
url=http://localhost
port=7546
minter=0x56Dc6FF4ECE4FAf7ABCa8841a9E7C1bF353d2676
contract=0xb701D34D42B08FF5DE922A536C9e76fADddCfCD3
contract_abi=solidity/contracts/GameToken.abi.json
```

### external-provider
For public Ethereum network external providers, such as [Infura](https://infura.io/), can be utilised to avoid running a full Ethereum node. For external providers the additional option is:

- **private_key** the private key of the minter account used to sign the transaction;

Specifically, when using the Infura endpoints, please use the websocket version only, so that the events emmitted can be listened properly. And an example of that can be found in the `[infura]` part of the sample configuration `local-config.cfg`, just like the following.

```
[infura]
type=ethereum
url=<infura-endpoint>
private_key=<private-key-of-minter>
minter=0xb16c872270E6F68777ff594cCD6653cC51fa3840
contract=0x33d6fc7943D420a993B1314b7387a13c2bC475D5
contract_abi=./solidity/contracts/DataTransceiver.abi.json
```

- **password** the password of the minter account to sign transaction

Similarly, the above option can be included in the configrations:

```
password=<password-of-minter-account>
```

With this configuration, the Ethereum adapter will try to unlock the minter account with password to sign a transaction.

- **poa** boolean to indicate whether to enable the injection of PoA middleware

For networks that supports Proof-of-Authority (PoA) standard, such as the Rinkeby test network, the above option can be included in the configurations to allow modification on the block data that has deviation from the Ethereum yellow paper specification. Example is simply given as:

```
poa=true
```

To facilitate the test, deployment to the public network is also enabled by using the truffle installed. Before that, one has to fill in the correct `MNEMONIC` and `API_KEY` in the `solidity/truffle-config.js` file. Here it is assumed that public test network `rinkeby` will be used, but one change that to the need.

```
npx truffle migrate --reset --network rinkeby
```

## Usage
The usage of the interledger component to interact with the Ethereum networks requires having the data sender or receiver which implement the `InterledgerSenderInterface` or `InterledgerReceiverInterface` properly deployed. With the sender and receiver set up, the interledger component can then be instantiated to connect to them. After that, by emitting the specifc event described above, the data payload can be transferred and observed accross the two ledgers via the component.

### Examples

- [Transfering Data](./example-data_transfer.rst) from one ledger to another.
- [Game Asset Transfer](./example-game_asset_transfer.rst) example provides functionality for managing in-game assets: the assets can either be used in a game or traded between gamers. For both activities, a separate ledger is used and Interledger ensures that each asset is active in only one of the ledgers.

