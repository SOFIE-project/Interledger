################################################
Example: Utilising Interledger for Data Transfer
################################################

Overview
========

The SOFIE Interledger component supports atomic transfer of information between ledgers.

Goal
-----

This example implements data transfer functionality between two ledgers. The example contains code for the Ethereum and Hyperledger Fabric ledgers, and other types of ledgers can be utilised with simple configuration changes.

Design
------

A smart contract `DataSender`_ that implements the `InterledgerSenderInterface`_ is deployed on the *Initiator* ledger to invoke the data sending process after the *emitData(bytes memory data)* function is called:

.. code-block::

    /**
     * @dev application logic to emit data to another ledger via event
     * @param data encoded data content in bytes
     */
    function emitData(bytes memory data) public {
        id += 1;
        emit InterledgerEventSending(id, data);
    }

A Hyperledger Fabric `DataSender-Fabric`_ chaincode for the same purpose includes the following:

.. code-block::

    // This is the application logic to emit data to another ledger via event, assumes the paramter below
    // @param data encoded data content in byte string
    func emitData(stub shim.ChaincodeStubInterface, args []string) error {
        var id1 uint64
        var data1 string
        ...
        data1 = args[0]
        id1 += 1
        ...
	    _ = stub.SetEvent("InterledgerEventSending", payload_event)
        ...
    }

On the receiving ledger, a smart contract `DataReceiver`_ that implements the `interledgerReceiverInterface`_ is deployed to receive the incoming data payload:

.. code-block::

    struct DataItem {
        uint256 nonce;
        bytes data;
    }

    // sample storage of data for application logic
    DataItem[] public dataItems;

    function interledgerReceive(uint256 nonce, bytes memory payload) public {
        dataItems.push(DataItem(nonce, payload));
        emit InterledgerEventAccepted(nonce);
    }

A Hyperledger Fabric `DataReceiver-Fabric`_ chaincode for the same purpose includes the following:

.. code-block::

    // This is the function to receive data from Interledger, which assumes the following parameters to be passed.
    // @param nonce The unique identifier of data event
    // @param data The actual data content encoded in byte string
    func interledgerReceive(stub shim.ChaincodeStubInterface, args []string) error {
        var nonce uint64
        var data string
        ...
        stub.PutState("items", payload)
        ...
        _ = stub.SetEvent("InterledgerEventAccepted", nonce_bytes)
        ...
    }

.. _DataSender: ../solidity/contracts/DataSender.sol
.. _DataSender-Fabric: ../fabric/chaincode/src/data_sender/data_sender.go
.. _DataReceiver: ../solidity/contracts/DataReceiver.sol
.. _DataReceiver-Fabric: ../fabric/chaincode/src/data_receiver/data_receiver.go
.. _InterledgerSenderInterface: ../solidity/contracts/InterledgerSenderInterface.sol
.. _InterledgerReceiverInterface: ../solidity/contracts/InterledgerReceiverInterface.sol

Data transfer between Two Ethereum ledgers
==========================================
This section details how to setup and run data transfers between two Ethereum ledgers (networks).

Set up
------

After the `DataSender`_ and `DataReceiver`_ have been deployed in the respective Ethereum networks, a configuration file similar to the one below is required for connecting the two smart contracts to the interledger component (i.e. it defines an *Interledger instance* between the two smart contracts ).

::

  [service]
  direction=left-to-right
  left=left
  right=right

  [left]
  type=ethereum
  url=http://localhost
  port=7545
  minter=<minter_address>
  contract=<contract_address>
  contract_abi=solidity/contracts/DataSender.abi.json

  [right]
  type=ethereum
  url=http://localhost
  port=7546
  minter=<minter_address>
  contract=<contract_address>
  contract_abi=solidity/contracts/DataReceiver.abi.json

For the corresponding Hyperledger Fabric chaincodes, please follow the adapter-specific documentation of `Fabric`_ for configuration and other details.

.. _Fabric: ../doc/adapter-fabric.md

Execution
---------

1. Start the Interleldger component (and the defined *Interledger instance*).

::

  python3 start_interledger.py config-file-name.cfg

Interledger will then listen for the "InterledgerEventSending" event, and once it catches the event, forward the data payload of that event to the data receiver.

2. Invoke the "emitData" method of the data sender (any suitable means can be used) to trigger the data transfer.

3. The response events of "InterledgerEventAccepted" or "InterledgerEventRejected" and the storage of the incoming data can then be observed on the destination ledger.


Data transfer between Hyperledger Fabric and Ethereum
=====================================================

This section details how to run data transfers between an Ethereum and a Hyperledger Fabric ledgers, this time as a bidirectional connection utilising two *Interledger instances* in opposite directions.

Set up
-------

First, the Hyperledger Fabric and Ethereum networks on both sides of the Interledger component should be set up, upon which the chaincode and/or smart contract for data sender and receiver can be deployed.

For Hyperledger Fabric, a procedure similar to the one described in `Adapter-Fabric`_ should be followed. In this, tests for the deployment of chaincodes for both data sender and receiver will be covered by the `test-script`_. Note that the chaincode deployment may take a while to settle.

.. _Adapter-Fabric: ./adapter-fabric.md#Network-set-up
.. _test-script: ../tests/fabric/data_transfer_hf_eth.py

For Ethereum side, private test networks can be easily set up as follows.

::

    ganache-cli -p 7545 -b 1
    ganache-cli -p 7546 -b 1

The smart contracts for data sender and receiver could be deployed as follows.

::

    truffle migrate --reset --f 2 --to 2 --network left
    truffle migrate --reset --f 3 --to 3 --network right


After the migrations settle, the corresponding configuration file `local-config-HF-ETH.cfg` should be updated for corresponding sections, including `right1` for the data receiver and `left2` for data sender.

Execution
---------

With the networks set up and smart contracts deployed, it is ready to test for data transfers between:

1. Hyperledger Fabric (left1) to Ethereum (right1) networks
2. Ethereuem (left2) to Hyperledger Fabric networks

with the following commands

::

    export PATH=$PATH:$PWD/fabric/bin
    python tests/fabric/data_transfer_hf_eth.py local-config-HF-ETH.cfg 

The actions of data payload being transferred between the two types of distributed ledgers can be observed from the standard outputs.
