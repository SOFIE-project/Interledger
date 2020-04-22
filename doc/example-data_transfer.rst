################################################
Example: Utilising Interledger for Data Transfer
################################################

Overview
========

The SOFIE Interledger component supports atomic transfer of information between ledgers.

Goal
-----

This example implements data transfer functionality between two Ethereum networks. Other types of ledgers can be utilised with simple configuration changes.

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


.. _DataSender: ../solidity/contracts/DataSender.sol
.. _DataReceiver: ../solidity/contracts/DataReceiver.sol
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


Execution
---------

1. Start an instance of the Interleldger component that connects to the specified smart contracts for data sending and receiving.

::

  python3 start_interledger.py config-file-name.cfg

Interledger will then listen for the "InterledgerEventSending" event, and forward the data payload of that event to the data receiver once it catches the event.

2. Invoke the "emitData" method of the data sender (any suitable means can be used) to trigger the data transfer.

3. The response events of "InterledgerEventAccepted" or "InterledgerEventRejected" and the storage of the incoming data can then be observed on the destination ledger.
