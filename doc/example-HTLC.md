# Example: Hash Time Locked Contracts (HTLCs) with Interledger

[Hash Time Locked Contracts](https://en.bitcoin.it/wiki/Hash_Time_Locked_Contracts) (HTLCs) allows parties (Alice and Bob in this example) to exchange assets securely on a ledger. Hash-locks are cryptographic locks, which can be unlocked by providing a secret whose hash matches the value configured in the hash-lock. HTLCs are implemented as smart contracts: assets destined to parties of exchange are protected by the same lock value in two different contracts. Therefore after Alice that knows the secrect, reveals it to withdraw assets, Bob can use the revealed secret to withdraw assets from another contract, therefore there is no risk for Bob to be cheated. Assets are also time-locked, if the withdrawal does not happen within a certain timeframe, the party that originally deposited assets to the contract can get its assets back. HTLCs can be used to exchange any kind of ledger-based assets, including cryptocurrencies, tokens such as ERC20 or ERC721, etc.

If assets reside on different ledgers, SOFIE Interledger component can be used to automate the last step of transaction: after Alice reveals the secret while withdrawing assets, Interledger will forward the secret to another ledger, which will trigger withdrawal of Bob's assets.

## Overview of the HTLC-based asset exchange with Interledger

Figure 1 below shows in more detail how the [HTLC smart contract](/solidity/contracts/HTLCEth.sol) for Ethereum works with Interledger.

![Interledger](/figures/Interledger-HTLC.png)
Figure 1: Interledger with Hash Time Locked Contracts

1. First Alice chooses secret *s* and calculates *H(s)*.

2. Alice and Bob agree on exact terms of asset exchange and Alice communicates *H(s)* to Bob.

3. Alice deposits funds destined to Bob in Ledger A by paying funds to *depositFunds(Bob's address, H(s), refund time)* function of HTLC contract. The refund time is the timestamp after which funds can be recovered by Alice.

4. Bob deposits funds for Alice in Ledger B in a similar way, except for security reasons the refund time for Bob's deposit should be somehow earlier compared to Alice's one. Otherwise Alice can retrieve funds from Ledger B at the last possible moment, and immediately afterwards, before Bob has a chance to react, can receive refund from Ledger A.

5. Alice initiates the transfer by calling the *withdrawFunds(H(s), s)* function of HTLC contract on Ledger A.

6. HTLC contract verifies that hash of secret *s* matches predefined lock value *H(s)* and:
   1. Transfers funds (that were originally deposited by Bob) to Alice's address on Ledger A.

   2. Also emits *InterledgerEventSending(Bob's address, (H(s), s)* event. Both the lock value *H(s)* and secret *s* as encoded in the [data parameter](Interledger_internals.rst#sender-interface) of the event.

7. The Interledger component is configured to interact with HTLC contracts on both ledger. After receiving the event from the Ledger A, Interledger calls the *interledgerReceive(nonce, (H(s), s)* function of the HTLC contract on ledger B.

8. The *interledgerReceive()* function unpacks the lock value and secret, and calls the *withdrawFunds(H(s), s)* function from the same contract, which in turn transfers the funds (that were originally deposited by Alice) to Bob's address on Ledger B. It is important to note that also third parties (Interledger component in this case) can trigger transfer of assets by providing a correct secret to the HTLC contract.

For clarity, the rest of Inteledger-related events and functions, such as emitting *InterledgerEventAccepted()* and calling *interledgerCommit()* are not shown the figure.

If the transfer of assets does not happen (the secret *s* is not revealed) before the specified refund time, both parties can recover their funds by calling *recoverFunds(H(s))* function of the HTLC contract to which they have deposited funds.

The current example HTLC contract supports exchange of Ethereum cryptocurrency (Ethers) and it can be easily extended to support any kind of ledger-based assets, which would allow e.g. to exchange Ethers on Ledger A for ERC721 tokens on Ledger B.

HTLCs together with Interledger enable flexible applications, for example, revealing a secret may trigger multiple transfers of assets, or the transfer of assets may trigger another action on a third ledger through the Interledger component. While in this example involved parties are people, parties of the asset exchange can also include, e.g., a device or smart contract acting on a behalf of the person or organisation, which in turn enables a high-level of automation.


## Interledger configuration

The Interledger component is configured normally as described in the main [README](/README.md#configuration). In this HTLC example, Interledger should be unidirectional, e.g. if Alice's ledger is `left` and Bob's ledger is `right`, then the direction should be `right-to-left`.
