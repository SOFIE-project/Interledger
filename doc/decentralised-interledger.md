# Decentralised Interledger

## Motivation

While the single node version of Interledger (IL) is capable of triggering transfer of information between distributed ledgers, an implicit assumption is that the party running the IL node can be trusted to promptly and correctly complete all transactions. Yet, even if the node is properly configured and can resist many attacks, a single node always forms a single point of failure.

*Decentralised Interledger (DIL)* reduces the trust requirement by building on redundancy, internal monitoring and recovery: the IL functionality is provided by a *consortium of partners* each running one or more IL nodes that continuously co-ordinate and monitor their actions using a shared state so that all operations are conducted under the observation of the whole consortium, and will be auditable by all afterwards. The parallelism in the DIL design also improves the robustness and throughput of the overall system as well. Switching to DIL in no way affects the external interfaces or use of the IL service, only the internal operations of IL, so to the users of the IL service the change only appears as a more robust and trustworthy operation of IL.

## Architecture overview

Overall the IL architecture remains very similar to the single node IL as all the changes required to support the DIL functionality only affect the IL Core, and all the ledger adapters and application smart contracts remain the same. The major change from a single node IL is that instead of the Core handing all transactions to the correct ledger adapter on the same node, it now writes the information to the shared state that keeps a shared records of transfers for all DIL nodes in the consortium and the node responsible for continuing the transaction (together with standbys) is then chosen in a pseudo-random manner (by using a deterministic algorithm and a hash function as the source of randomness). Further redundancy can be provided by having all capable nodes (nodes may have different capabilities and not all nodes necessarily can operate with all ledgers) monitor the related ledgers and competing to update the shared state. The architechture and transaction flow are detailed in Figure 1.

![DIL architecture and data flow](/figures/decentralized-interledger-architecture.png)
*Figure 1: Decentralized Interledger architecture and its typical data flow*

First, all capable nodes listen for events on the Initiator ledger (1) and compete to write it to the shared state (2) and then check that the successful write is correct. Using a deterministic algorithm a pseudo-randomly selected node is chosen to perform the Responder operations while others are chosen as backups (3). As the Responder operation may be a multi-ledger operation that can take a while to complete, the chosen Responder will first signal that it will proceed with the operation (4) and then proceed with the Responder operations of the transaction (5-6, multi-ledger operations will have further steps due to the two-phase commit), and once complete, it will write the result to the shared ledger (7) (if steps 4 or 7 time out, the first backup node will take over steps 4-7 etc.). An Initiator node is chosen using the same algorithm (8), but this time it will not write a separate acceptance to the shared ledger as the Initiator operation is much faster to complete involving only submitting the result to the Initiator ledger (9) and updating the shared status (10-11) (again, if step 11 times out, the first backup will step in etc.).

The state management layer can be implemented using multiple technologies. Figure 1 shows a consortium ledger, such as Hyperledger Fabric that is hosted by all the parties, but a shared trusted traditional database could also be used e.g. when all the nodes are run by a single organization. Regardless of the technology, the DIL nodes carry out the transfer operations by creating, reading and updating the transfer entries in the state management layer. The auditing is carried by checking the same entries against the ledgers connected to the initiators and responders.

This DIL architecture provide the following major benefits compared to the single node IL implementation:

- Distributed trust: the level of trust required on the users of the IL service is reduced by introducing a consortium state management, which enables auditability as well.

- Robustness by redundancy: no longer will the crash of a single IL node crash the whole IL service and the shared state speeds up the recovery of the crashed node.

- Throughput improvement: the transfer operations can be carried out parallelly by randomly selecting among all the running DIL nodes, enhancing the overall throughput of the interledger system.


## Implementation status

The development work is ongoing and currently the initial implementation supports all the single-node functionalities *except multi-ledger operations* (to be added shortly).

The new DIL features are also being added in stages and currently the initial implementation supports the following DIL properties:

- a proof-of-concept *local state adapter* is already available for testing purposes - it essentially runs the DIL functionality as a single-node implementation and does not support coordinating multiple nodes. The Hyperledger Fabric  and a relational database (SQL) versions of the state adapter (that provide the support for multiple nodes) are currently under development.

- The Initiator adapters of all nodes listen for new transactions (i.e. all nodes are assumed to connect to the same Initiator ledger(s)) (step 1) and compete to write the information to the shared state as well as monitor that the succeeding write was correctly performed (step 2). Future versions will support nodes with differing Initiator ledger support.

- The Responder adapters of all nodes ae assumed to be able to act as backups (i.e. all nodes are assumed to connect to the same Responder ledger(s)) if the chosen Responder fails to accept the transaction in time (step 4), but after that they only monitor the shared state (and not the ledger in question) for the transaction completion (step 7) and the backup will take over if step 7 is not completed in time. Future versions will support nodes with differing Responder ledger support.

- once the Initiator adapter to complete the transaction has been chosen (step 8), all other nodes only monitor the internal state for the completion of the transaction (step 11) and step in as backups if the transaction is not completed in time. Future versions will support nodes with differing Initiator ledger support.



