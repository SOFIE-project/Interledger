.. _smart_contracts:

===================================
Interledger smart contracts
===================================

This page lists the smart contracts used in Interledger.

The *StateContract* contract exposes an interface composed by data structure, events and functions to support the Interledger protocol :ref:`interledger`. 

The *GameToken* contract implement a ERC721 token and implements the *StateContract* in order to be used in the Interledger protocol.

------------------
Code documentation
------------------

^^^^^^^^^^^^^
StateContract
^^^^^^^^^^^^^

.. autosolcontract:: StateContract
    :members:

^^^^^^^^^^^^^
GameToken
^^^^^^^^^^^^^

.. autosolcontract:: GameToken
    :members: