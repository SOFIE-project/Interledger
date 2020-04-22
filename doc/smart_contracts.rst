.. _smart_contracts:

===================================
Interledger smart contracts
===================================

This page lists the smart contracts used in Interledger.

The *InterledgerSenderInterface* describes the sender's interface of 
:ref:`Interledger protocol <interledger>`.

The *InterledgerReceiverInterface* describes the receiver's interface of 
:ref:`Interledger protocol <interledger>`.

The *DataSender* contract is a simple implementation of *InterledgerSenderInterface*.

The *DataReceiver* contract is a simple implementation of *InterledgerReceiverInterface*.

The *DataTransceiver* contract implements both *InterledgerSenderInterface* and 
*InterledgerReceiverInterface*.

The *AssetTransferInterface* contract describes the methods, data structure and events to manage 
state transition of assets.

The *GameToken* contract implement a ERC721 token and implements the *AssetTransferInterface*,
*InterledgerSenderInterface*, and *InterledgerReceiverInterface* in order to be used 
by the Interledger.

------------------
Code documentation
------------------

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
InterledgerSenderInterface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosolcontract:: InterledgerSenderInterface
    :members:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
InterledgerReceiverInterface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosolcontract:: InterledgerReceiverInterface
    :members:

^^^^^^^^^^^^^
DataSender
^^^^^^^^^^^^^

.. autosolcontract:: DataSender
    :members:

^^^^^^^^^^^^^
DataReceiver
^^^^^^^^^^^^^

.. autosolcontract:: DataReceiver
    :members:

^^^^^^^^^^^^^^^
DataTransceiver
^^^^^^^^^^^^^^^

.. autosolcontract:: DataTransceiver
    :members:

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssetTransferInterface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosolcontract:: AssetTransferInterface
    :members:

^^^^^^^^^^^^^
GameToken
^^^^^^^^^^^^^

.. autosolcontract:: GameToken
    :members:
