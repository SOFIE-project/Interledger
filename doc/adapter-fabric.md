# Interledger support for HyperLedger Fabric networks

The Interledger component enables the interaction with HyperLedger Fabric networks in both the *Initiator* and *Responder* roles. The Interledger for the moment supports only HyperLedger Fabric with version 1.4.x.

## Interfaces for transfer

### Sending

The data sending interface `InterledgerSender` as shown in the chaincode [`data_sender.go`](../fabric/chaincode/src/data_sender/data_sender.go) is implemented by the *Initiator* chaincode, for instance `DataSender` in the same source file.

To trigger the sending action accross ledgers, the data payload should be included in the event `InterledgerEventSending`, where the `Id` is the identifier of the data sending event, while the bytes `Data` is the actual data to be sent.

Once the data has been processed by the *Responder* side, the resulting status (Accept/Reject) is reported back to the *Initiator* side using the `interledgerCommit` or `interledgerAbort` methods.

### Receiving

The data receiving interface `InterledgerReceiver` as shown in the chaincode [`data_receiver.go`](../fabric/chaincode/src/data_receiver/data_receiver.go) is implemented by the *Responder* chaincode, for instance `DataReceiver` in the same source file.

The method `interledgerReceive` is used to receive data from the interledger component to the ledger, where the `Nonce` is unique identifier of the data transfer object inside the Interledger. The storage or processing logic can be added and customized here before replying whether the incoming data payload is accepted or rejected by the application logic of the chaincode, which is indicated using the events `InterledgerEventAccepted` or `InterledgerEventRejected`.

## Prerequisites

The HyperLedger Fabric adapter of the Interledger component requires the HyperLedger Fabric binaries to work as expected.

To have the necessary binaries ready, run the following command to install HyperLedger Fabric before running the Interledger with adapter connected to HyperLedger Fabric networks.

```
cd fabric
curl -sSL https://raw.githubusercontent.com/hyperledger/fabric/master/scripts/bootstrap.sh | bash -s -- 1.4.7
mv fabric-samples/bin/ ./bin/
rm -rf fabric-samples/
```

This way, the binaries are ready and available for use.

## Configurations

The configuration information of the networks is to be included in a config file that is passed to the component. The HyperLedger Fabric network can be on both sides of the component, so all `direction` options (`left`, `right` or `both`) are possible.

For `type` =  `fabric`, the required options are:

- **network_profile:** A network connection profile helps the SDK used to connect to the fabric network by providing all required information to operate with it;
- **channel_name:** The name of the channel to interact with;
- **cc_name:** the chaincode name;
- **cc_version:** the chaincode version;
- **org_name:** Organization name;
- **user_name:** User name;
- **peer_name:** Peer name.

Example of the related sections in an Interledger configuration file *config-file-name.cfg*:

```
[service]
direction=left-to-right
left=left
right=...

[left]
type=fabric
network_profile=fabric/fixtures/network.json
channel_name=mychannel
cc_name=data_sender
cc_version=v1.0
org_name=org1.example.com
user_name=Admin
peer_name=peer0.org1.example.com

...
```

## Usage

With configuration files matching the HyperLedger Fabric network used, as illustrated by the sample above, the Interledger component can be used the same way as with other ledger types, such as Ethereum and KSI, using the starting script below.

```
python3 start_interledger.py config-file-name.cfg
```

The usage of the interledger component to interact with the HyperLedger Fabric networks requires having the data sender or receiver side that implements the `InterledgerSender` or `InterledgerReceiver` interfaces mentioned above deployed beforehand. 

With the sender or receiver set up, the interledger component can then be instantiated to connect to the corresponding initiator or responder respectively. After that, by emitting the specifc event described above, the data payload can be transferred and observed accross the two ledgers via the component.



### Example of data transfer

A concrete sample usage of simple data transfer is demonstrated here for illusration.

#### Network set up

```
export HLF_VERSION=1.4.7

docker pull hyperledger/fabric-peer:${HLF_VERSION}
docker pull hyperledger/fabric-orderer:${HLF_VERSION}
docker pull hyperledger/fabric-ca:${HLF_VERSION}
docker pull hyperledger/fabric-ccenv:${HLF_VERSION}

docker-compose -f fabric/fixtures/docker-compose-2orgs-4peers-tls.yaml up
```

#### Chaincode deploy

Under virtual environment, run the following in the project directory to add the Fabric binaries into `PATH`.

```
export PATH=$PATH:$PWD/fabric/bin
```

To set up the HyperLedger Fabric network with the related chaincode deployed, run the following commands under project root. Here it is assumed the network is up as in the step above.

```
python tests/fabric/fabric_setup.py local-config-fabric.cfg
```

After this deployment, the Interledger component can be instantiated and get running to enable the data transfer across HyperLedger Fabric networks.

Note that to have a clean setup with no previous deployment, one can easily clean up the related containers of the network, for example run the `docker system prune` command.

#### Transfer via the Interledger

To run the demo of data transfer across HyperLedger Fabric networks, run the following command under the project root, since the setting of configurations assumes such.

```
python tests/fabric/interledger_fabric.py local-config-fabric.cfg
```

The script above will get an instance of the Interledger component running, both the left and right side of which is connected to the same HyperLedger Fabric network in this case, for simplicity. Note that this script will implicitly run the `tests/fabric/fabric_setup.py` mentioned in the chaincode deployment section, so it does the deployment and demomenstrates the data transfer process enabled by the Interledger component. Thus, to re-run this demo, one needs to set up the clean networks again.

The running instance will listen on the events that are emitted from the specified channel and chaincode.

Then, the same script will emit an event with sample payload data. In the terminal, the transfer process across HyperLedger Fabric network invoked by the event can be observed.