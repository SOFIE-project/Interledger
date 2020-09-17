# Multi-ledger operation

## Motivation

By default, the Interledger component supports dual-ledger transaction, namely that there is only one initiator and one responder, each conneted to distributed leddger. It is possible to have multiple instances of the Interledger component running simultaneously, and forming parallel group when those listen for the same trigger, or call the same responder. Naturally, those nodes in the above parallel group can be utilized to conduct the AND/OR operations. 

In theory, all multi-ledger transaction can be realized by combination of dual-ledger transactions and some customization of the smart contracts on the ledger. However, this may be inefficient for processing speed, expensive in cost and holds assumption of logic dependency among ledgers or smart contracts. Having the multi-ledger support in the Interledger core, makes the processing faster and cheaper, at the same time decouples the application logic among ledgers or contracts.

## Design choices

### Multiple triggers

Simple observation on the building block of the Interledger component for dual-ledger transaction, implies that the multi-trgger logic can be complicated, especially when the data payload from any two triggering events are different, it is difficult to decide what information to be passed to Interledger and the responder ledgers connected. 

It is better to introduce an intermediate smart contract to pre-process the incoming data from different ledgers, and transfer a unified event to its responders, the payload of which would be highly application-specific. Having a smart contract for this responsibility is highly flexible to reduce the complexity here, while additional cost and processing time is required. 

### Multiple responders

Havign multiple responders for a single trigger is much easier to be realized, either when all feedbacks are required to be positive for a commit on the initiator (thus an AND operation), or when only a fraction of the feedbacks to be postive (K-out-of-N operation). The interledger core just needs to check the results of the transactions from the responders to decide whether to commit or abort the transaction.

## Implementation

The mode of multi-ledger operation and the threhold number of positive responses for commiting a multi-ledger transaction can be given via a configuration file that is used by the starting script, same as the dual-ledger case. And this information is then passed and saved in the Interledger instance as filed of `Interledger.multi` to indicate whether the multi-ledger mode is toggled or not. And of course, the `Interledger.responders` is used when the multi-ledger mode is on.

### Transfer object

An addiontal field of `send_tasks` and `results` have been added to the `transfer` object for the list of processing tasks and action results from the responders. The transfer state has the following changes:
  - Add `State.ENOUGH_RESPONDED`
  - `State.RESPONDED` -> `State.ALL_RESPONDED`

### Processing

Under multi-ledger mode, now `Interledger.send_transfer()` will have each of its responder invoking the `send_data()` method. As the next step, `Interledger.transfer_result()` will first get the results of the newly finished `send_tasks`; then update the `transfer.STATE` if requirements met. Fianlly, the `Interledger.process_result()` will iterate through the list of transfers that have been responded to decide the commit or abort operation.

### About KSI

A difference is to be noticed between the multi-ledger mode and dual-ledger one is when the KSI resonder is used. For the moment, the multi-ledger case will ignore the transaction hash from each of the KSI responders, since the responses of each would be different.

## Usage

The detailed usage of the multi-ledger operation mode can be found at the [main documenation](/README.md#usage).
