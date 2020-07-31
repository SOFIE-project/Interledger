################################################
Example: Utilising Interledger for Data Transfer
################################################

Overview
========

The SOFIE Interledger component supports atomic transfer of information between ledgers.

Goal
-----

This example implements data transfer functionality between two Ethereum networks. Other types of ledgers e.g. Hyperledger Fabric networks can be utilised with simple configuration changes.

Design
------

A smart contact `DataSender`_ that implements the `InterledgerSenderInterface`_ is deployed on the originating network to invoke the data sending process after the *emitData(bytes memory data)* function is called:

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

Usage
======

Set up
------

After the `DataSender`_ and `DataReceiver`_ have been deployed in the respective Ethereum networks, a configuration file similar to the one below should be provided for connecting the two smart contracts to the interledger component.

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

1. Start an instance of the Interleldger component that connects to the specified smart contracts for data sending and receiving.

::

  python3 start_interledger.py config-file-name.cfg

Interledger will then listen for the "InterledgerEventSending" event, and forward the data payload of that event to the data receiver once it catches the event.

2. Invoke the "emitData" method of the data sender (any suitable means can be used) to trigger the data transfer.

3. The response events of "InterledgerEventAccepted" or "InterledgerEventRejected" and the storage of the incoming data can then be observed on the destination ledger.

Note: for the data transfer between a Hyperledger Fabric and a Ethereum network in both directions, the detailed description is provided in `HF-ETH-Data-transfer-example`_.

.. _HF-ETH-Data-transfer-example: ../doc/example-data-transfer-HF-ETH.md