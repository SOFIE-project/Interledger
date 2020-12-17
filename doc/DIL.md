# Decentralized Interledger

## Motivation

While the single node version of Interledger (IL) is capable to trigger transfer of information across distributed ledgers, an implicit assumption is that the running party behind the IL should be trusted in the whole process. This means the IL node will not be corrupted by malicious party, thus misbehaving by transferring incorrect transfer payload to a target ledger, or stop the transfer from being sent at all. Not to mention the risk of IL process crashing can become a single point of failure in the system.

Decentralized Interledger (DIL) shards the trust to all participating parties involving a interledger operation, so that the operation process is conducted under the observation of all, and will be auditable by all afterwards. The intrinsic parallelism in the DIL design improves the robustness and throughput of the overall system as well.

## Architecture overview

To achieve the above ends, the DIL introduced a state management layer to provide the shared records of transfers for all DIL nodes controlled by corresponding parties. Compared to single node version of IL implementation, the DIL will always manipulate the transfer entries from and to the state management layer, so that all the DIL nodes have consensus on the status and data payload of the transfer entries. 

![DIL architecture and data flow](/figures/DIL-architecture.png)
Figure 1: Decentralized Interledger architecture and its typical data flow

As shown in the Figure 1, the state management layer can be a consortium distributed ledger, such as Hyperledger Fabric that are hosted by all the parties; or a shared trusted traditional database, say for instance if all the nodes are run by a single oranization. This way, the DIL nodes can act the transfer operations by creating, reading and updating the transfer entries in the state management layer. The auditing is carried by checking the same entries against the ledgers connected to the initiators and responders.

## Implementation

The development work is still in progress. More detais will be revealed later.

## Functionalities

The DIL architecture described above provide the following major benefits, in addition to the single node IL implementation.

- Distributed trust

  The required trust on a single node of IL is sharded and reduced by introducing a consortium state management, which enables auditability as well.

- Robustnenss by redundancy

  No longer will the crash of an IL node be a single point of failure. Besides, the recovery of a DIL node is allowed by the shared state.

- Throughput improvement

  The transfer operations can be carried out parallelly by randomly selecting among all the running DIL nodes, enhancing the overall throughput of the interledger system.



