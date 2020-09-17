=============================================
Example: Game Asset Transfer Protocol with Interledger
=============================================

The SOFIE Interledger component can be utilized to enforce the transfer of in-game assets between two ledgers in an atomic manner. A private ledger *A* is used to track assets used inside the game, but in order to allow players to also trade their assets in a flexible way, a public ledger *B* is used. However, if the asset is being traded, it should be not be usable inside the game as the the asset's owner may change at any moment. Therefore, the asset should be in the active (usable) state at most in a one ledger. The Interledger component can be used to implement such state transfer protocol with only a slight modification of the basic `data transfer`_ smart contract. 

An implementation of the described asset transfer protocol for Ethereum, based on `AssetTransferInterface`_, is available in `GameToken.sol`_.

.. _data transfer: ../solidity/contracts/DataTransceiver.sol

.. _AssetTransferInterface: ../solidity/contracts/AssetTransferInterface.sol

.. _GameToken.sol: ../solidity/contracts/GameToken.sol


State machine based protocol
----------------------------

Since the data stored in a ledger (such as a blockchain) cannot be removed, the transfer of ledger-based assets can be considered to be "logical": the asset has a label such as "Here" and "NotHere" to represent its "presence", or "absence", in each of the ledgers. These labels are referred to as **states**.

The `GameToken.sol`_ smart contract implements a **state machine** in order to switch the states of the assets correctly. The smart contract together with the Interledger component guarantees that an asset can have a state "Here" in at most in one of the two ledgers at any point of time.

.. _states-single:

States of an asset
^^^^^^^^^^^^^^^^^^

.. figure:: ../figures/example-game_asset_transfer-local_states.png

The figure above shows the states a single asset can have in a ledger:

- **Here:** the asset is present in this ledger;
- **TransferOut:** the asset is "moving out" from this ledger (this state is used only for rolling back the transaction in case of errors);
- **NotHere:** the asset is present in another ledger.

In this context, we have two actors:

- **Asset creator (minter):** the entity in charge of creating (minting) new assets;
- **Asset owner:** the entity that owns an existing asset.

The creator of the asset is e.g., a gaming company, and it is the party in charge of running the Interledger component. The owner of an asset can use it only in the ledger in which it is present (has the status **Here**). To move that asset between ledgers, a cooperation between asset creator and owner is necessary to guarantee atomicity and security of the transfer operation. In practice, Interledger performs all actions required from the creator.

.. _states-global:


State View
^^^^^^^^^^

.. figure:: ../figures/example-game_asset_transfer-global_states.png

The state of an asset is the composition of the states of that asset in each ledger: **(state_ledger_A, state_ledger_B)**. For example, the state of an asset can be (Here, NotHere) or (NotHere, TransferOut).

During the transfer of an asset, the following **invariant** must be preserved:

``#states("Here") = 1 or (#states("Here") = 0  &&  #states("TransferOut") = 1)``

For example (states of the asset in both ledgers are shown in parentheses):
1) (Here, Here) breaks the invariant because ``#states("Here") = 2``;
2) (TransferOut, TransferOut) breaks the invariant because ``#states("Here") = 0  &&  #states("TransferOut") = 2``.

The **exception** is when an asset does not exist: in that case, we have ``#state("NotHere") = 2``

.. _states-interfaces:

State Interfaces
^^^^^^^^^^^^^^^^

The state definition of an asset is exposed by a smart contract running in each ledger. Each smart contract should provide the 4 methods to switch between the proposed states. One of the methods is only callable by the asset owner:

- ``transferOut(id)``: starts the asset transfer by setting the asset state of a present asset to **TransferOut** on the *Initator* ledger

The other three are only callable by the asset creator (minter) (in practice, they are called by the Interledger as a proxy for the creator):

- ``interledgerReceive(id)``: sets the asset state to **Here** on the *Responder* ledger.

- ``interledgerCommit(id)``: sets the asset state to **NotHere** on the *Initiator* ledger after a successful ``interledgerReceive(id)``.

- ``interledgerAbort(id, reason)``: reverts the asset state to **Here** after a failed ``interledgerReceive(id)``.

where ``id`` is an id identifying the involved asset.


Scenario 1: Successful Transfer
+++++++++++++++++++++++++++++++

An user *U* wants to transfer asset *asset1* (with id: assetId) from ledger A to ledger B.

**Precondition:** ``state(assetId) in ledger A = Here`` **&&** ``state(assetId) in ledger B = NotHere``

**Trigger:** The user *U* switches the state of *asset1* from ``Here`` to ``TransferOut`` in ledger A by invoking the ``transferOut(assetId)`` operation of the smart contract.

**Action:** The Interledger component calls ``interledgerReceive()`` function from ledger B, which switches the state of *asset1* from ``NotHere`` to ``Here`` in ledger B, and emits ``InterledgerEventAccepted()`` event to signal successful reception. 

After that, the Interledger component calls ``interledgerCommit()`` function in ledger A, which de-activates *asset1* by switching its state from ``TransferOut`` to ``NotHere``.

These two operations are atomic: either both or none are finalised. At each step, **global invariant** is preserved as introduced in `State view`_ section.

**Postcondition:** ``state(assetId) in ledger A = NotHere`` **&&** ``state(assetId) in ledger B = Here``


Scenario 2: Failed Transfer
+++++++++++++++++++++++++++

An user *U* wants to transfer asset *asset1* (with id: assetId) from ledger A to ledger B.

**Precondition:** ``state(assetId) in ledger A = Here`` **&&** ``state(assetId) in ledger B = NotHere``

**Trigger:** The user *U* switches the state of *asset1* from ``Here`` to ``TransferOut`` in ledger A by invoking the ``transferOut(assetId)`` operation of the smart contract.

**Action:** The Interledger component calls ``interledgerReceive()`` function from ledger B, which should set the state of *asset1* from ``NotHere`` to ``Here`` in ledger B, however this operation does not succeed (either transaction fails or  ``InterledgerEventRejected()`` event is emitted). 

After that, the Interledger component calls ``interledgerAbort()`` function in ledger A, which re-activates *asset1* by switching its state from ``TransferOut`` to ``Here``.

**Postcondition:** ``state(assetId) in ledger A = Here`` **&&** ``state(assetId) in ledger B = NotHere``

Using the Asset Transfer Functionality
--------------------------------------

The easiest way to test the Asset Transfer Functionality is to run a Interledger `CLI demo`_, which can also be run through Docker Compose setup described in the main `README`_.

.. _CLI demo: ../demo/cli/README.md

.. _README: ../README.md

For manual testing, setup and run the Interledger component as described in the main `README`_, and ensure that ``GameToken.sol`` is deployed on both ledgers, and the configuration file contains the correct address, minter, ABI entries for both ledgers.

Afterwards:

1. Mint new tokens by calling ``function mint(address to, uint256 tokenId, string memory tokenURI, bytes32 name)`` on both ledgers. The ``to`` parameter denotes the user of the token. This call must be run by the minter.

2. Set the state of one token to ``Here`` by calling ``function interledgerReceive(uint256 nonce, bytes memory data)`` on one ledger, where ``nonce`` can be any number and ``data`` is tokenId encoded with ``abi.encode()``. This call must be run by the minter.

3. Initiate the transfer by calling ``function transferOut(uint256 tokenId)`` on ledger in which the token is in ``Here`` state. This call must be run by the user.
