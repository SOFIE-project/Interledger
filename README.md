# SOFIE Interledger Component

## Table of Contents
- [Description](#description)
  * [Architecture Overview](#architecture-overview)
  * [Relation with SOFIE](#relation-with-sofie)
  * [Key Technologies](#key-technologies)
- [Usage](#usage)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Configuration](#configuration)
  * [Execution](#execution)
  * [Docker Images](#docker-images)
- [Testing](#testing)
  * [Prerequisites for Testing](#prerequisites-for-testing)
  * [Running the Tests](#running-the-tests)
  * [Evaluating the Results](#evaluating-the-results)
  * [Test for multi-ledgers-transaction](#test-for-multi-ledgers-transaction)
- [Generating Documentation](#generating-documentation)
  * [Requirements](#requirements)
  * [Generation](#generation)
  * [Miscs](#miscs)
- [Open Issues](#open-issues)
- [Future Work](#future-work)
- [Release Notes](#release-notes)
- [Contact Information](#contact-information)
- [License](#license)

## Description

This is the Interledger component of the [SOFIE Framework](https://github.com/SOFIE-project/Framework).

The Interledger component enables activity on an *Initiator* ledger to trigger activity on one or more *Responder* ledgers in an atomic manner. The ledgers can be of the same or different types (e.g. Ethereum, Hyperledger Fabric, Hyperledger Indy, or KSI), and once triggered, Interledger passes a customisable payload from the *Initiator* ledger to the *Responder* ledger(s). 

The distributed applications utilising the Interledger component can utilise the payload functionality to implement any customised features. Examples of how Interledger can be utilised include:
- [Transfering Data](/doc/example-data_transfer.rst) from one ledger to another.
- [Storing Data Hashes](/doc/adapter-ksi.md) stores detailed information in a (private) ledger and a hash of the information is then  stored in a (public) ledger at suitable intervals using Interledger to benefit from the higher trust of a public ledger.
- [Game Asset Transfer](/doc/example-game_asset_transfer.rst) implements a state transfer protocol, which is used for managing in-game assets: the assets can either be used in a game or traded between gamers. For both activities, a separate ledger is used and Interledger ensures that each asset is active in only one of the ledgers.
- [Hash Time Locked Contracts (HTLCs)](/doc/example-HTLC.md) describes how to use the Interledger to automate the asset exchange between two ledgers using Hash Time-Locked Contracs (HTLCs).

### Architecture Overview
The Interledger component can run one or more *Interledger instances* in parallel. Each instance provides a unidirectional transaction with clear roles: one ledger acts as the *Initiator* that triggers the transaction, and the other ledger(s) acts as the *Responder(s)* that reacts to the trigger. The *Initiator* can also send a data payload to the *Responder(s)*, but the *Responder(s)* can only reply a success/fail status, so the Interledger functions as a unidirectional data transfer from the *Initiator* to the *Responders*. However, a pair of ledgers can also be configured for bidirectional data transfer by defining two instances in opposite directions as described in the [Configuration](#Configuration) section. 

On some ledgers (e.g. Ethereum and Hyperledger Fabric), the Interledger communicates with an application smart contract on the ledger (the smart contract has to implement the *Initiator* and/or the *Responder* [interface](/doc/Interledger_internals.rst#ledger-interfaces)), while on others (e.g. Hyperledger Indy and KSI), no smart contract is required (or even available) and the Interledger communicates with the ledger directly. The ability to act as the Initiator and/or the Responder is normally included in the smart contract implementing the application logic, but separate proxy contracts can also be used as wrappers to interface with the Interledger component as has been done e.g. in the [Food Supply Chain pilot](https://media.voog.com/0000/0042/0957/files/sofie-onepager-food_final.pdf) (see the pilot's [smart contracts](https://github.com/orgs/SOFIE-project/projects/1) for details). 

![Interledger](figures/Interledger-overview-2.png)
*Figure 1: using the Interledger module*


As shown in figure 1, the Interledger component is run on a server and for each configured *Interledger instance* it listens for events (*InterledgerEventSending*) from the *Initiator*, which triggers the Interledger to call the *interledgerReceive()* function on the *Responder*. Once the *Responder* is finishied processing the transaction, it emits either *InterledgerEventAccepted* event, which triggers the Interledger to call *interledgerCommit()* function of the *Initiator*, or the *InterledgerEventRejected* event, which triggers the Interledger to call the *interledgerAbort()* function of the *Initiator*. If multiple responders have been defined in an instance, either all-N or k-out-of-N of them have to succeed (depending on which configuration was chosen), otherwise the whole transaction is aborted and the Interledger calls the *interledgerAbort()* function of the *Initiator*.

The *id* parameter of *InterledgerEventSending* is only for the *Initiator's* internal use: each transaction can have a unique *id* or multiple transactions can share the same *id* depending on the needs of the application smart contract. However, the *id* is not passed to the *Responder*, only the *data* parameter is (so if the *Initiator* wishes to send the *id* also to the Responder, it has to  be included in the *data* parameter). Internally, the Interledger component processes each transaction individually, so each transaction is given a unique *nonce*, which is used in all activities with the *Responder*. Finally, when the success/failure of the transaction is communicated back to the *Initiator*, the nonce is mapped back to the original *id*.

Internally, as shown in Figure 2, the Interledger component is composed of two types of elements:
- a single *core*  that manages the transactions between ledgers. It passes the transactions from the *Initiator adapter* to the correct *Responder adapter(s)* and the corresponding success/fail statuses back to the *Initiator adapter*, enforces the all-N and k-out-of-N rules for transactions with multiple responders, but does no processing on the data payload.
- *DLT adapters (Initiators and Responders)* links the core with the different ledger types. The adapter is responsible for translating between the core and the ledger's native commands (listening for events and calling functions). Normally, the adapter does no processing on the data payload, but it is possible to implement adapters with specific processing functionality, if the ledger itself lacks suitable functionality (e.g. the KSI Responder Adapter calculates a hash of the data payload and stores the hash to the KSI ledger).

<img width="75%" src="figures/Interledger-overview-1.png">

*Figure 2: internal structure of the Interledger module*

Interledger component currently supports three DLT types: [Ethereum](/doc/adapter-eth.md), [Hyperledger Fabric](/doc/adapter-fabric.md), [Hyperledger Indy](/doc/adapter-indy.md) and [KSI](/doc/adapter-ksi.md). For Ethereum and Hyperledger Fabric, both an *Initiator adapter* and a *Responder adapter* are provided, while for Hyperledger Indy, only a *Initiator adapter* is provided, and for KSI only a *Responder adapter*. Other DLTs can be supported by [implementing adapters](/doc/Interledger_internals.rst#extending-interledger-to-support-additional-ledgers) for them. Support for additional ledgers is [Future Work](#Future-Work).

More details of the Interledger component's implementation and how it is utilised for *one-on-one* and *multi-ledger* transactions can be found in the [Technical description](/doc/Interledger_internals.rst).

Finally, this repository mostly focuses on describing a *single-node* implementation of the Interledger functionality, i.e. where one party runs a single node that performs all Interledger operations, thus necessitating the users of the IL services to trust that party. Work has begun on a *Decentralised Interledger (DIL)* implementation, where a *consortium of parties* each can run one or more Interledger nodes all of which are co-ordinated using a shared state. This reduces the trust required as now the users of the Interledger services only need to trust the whole consortium, as well as improves throughput and resiliency of Interledger. An initial implementation of the [Decentralised Interledger (DIL)](/doc/decentralised-interledger.md) is now available. Specifically, the [interfaces](/src/interledger/adapter/interfaces.py) of state adapters are clearly defined at, and a proof-of-concept local state adapter is implemented and verified, with in-memory storage of the transfer entries. The Hyperledger Fabric version and relational database (SQL) version of the state adapter following the same interfaces are still under development. These work will continue in 2021 with more complete implementations, so for now, it's only recommended for testing purposes. Switching to DIL in no way affects the external interfaces or use of the Interledger service, only the internal operations of Interledger, so for the users of the Interledger service the change only appears as a more robust and trustworthy operation of Interledger.

### Relation with SOFIE
Interledger is a key component of the SOFIE Federation Architecture as it enables transactions across ledgers. It is a a standalone module that may be used by other SOFIE components and applications as necessary.


SOFIE pilots utilise the Interledger for different purposes, eg.g. the [Food Supply Chain](https://media.voog.com/0000/0042/0957/files/sofie-onepager-food_final.pdf) uses the Interledger  to automatically store hashes of the transactions on private ledgers onto a public Ethereum ledger for integrity verification, while the [Context-aware Mobile Gaming](https://media.voog.com/0000/0042/0957/files/sofie-onepager-gaming-noScreens.pdf) utilises Interledger to enforce that in-game assets are either available for gaming or being traded between gamers. 

### Key Technologies
The software modules are implemented in **Python**.
Currently the component supports the Ethereum ledger, and thus **Solidity** smart contracts, Hyperledger Fabric, as well as the KSI ledger.

***

## Usage

The `src/interledger` directory contains the code implementing the software modules of Interledger and the default adapters for Ethereum, Hyperledger Fabric and KSI.

The `solidity/contracts` contains the smart contracts including the data transfer interfaces used by the component.

### Prerequisites

Software modules: **Python 3.6**.

Smart contracts: **Solidity 0.5**.

Ganache CLI and Truffle to test Interledger locally.

### Installation

The dependencies of the Interledger component can be installed with the following commands (note that it is also possible to run the component using a docker image as described in the [Docker Images](#Docker-Images) section):

```bash
python3 setup.py develop # Install project dependencies locally
```

The following commands also apply.

```
python3 setup.py build
python3 setup.py install
```

#### Install Smart Contracts using NPM

Users who only need the essential smart contracts related to Interledger data or asset transfer interfaces and their example implementations have the option to use the separate [SOFIE Interledger Contracts npm module](https://www.npmjs.com/package/sofie-interledger-contracts), without the need to include this whole repository.

```bash
npm install sofie-interledger-contracts
```

This command installs the module with all the essential smart contracts of interfaces and sample implementations. These can then be extended for a custom application logic.

### Configuration
The configuration file, following the `ini` format, has three main sections:

1) `[service]`: defines the connected ledgers, `left` and `right`, and the `direction` of the data transfer;
    - `direction` = `both` | `left-to-right` | `right-to-left`
    - `left` = *left*
    - `right` = *right*

2) `[left]`: indicates the `type` of that ledger and lists its options. The options depend on the specific ledger.  
    - `type` = `ethereum` | `fabric` | `indy` | `ksi` | ...
    - ...

3) `[right]`: same as above.
    - `type` = `ethereum` | `fabric` | `indy` |`ksi` | ...
    - ...

The `direction` can have three values:
- `left-to-right` means that a single unidirectional *Interledger instance* is started so that it listens for events on the `left` ledger with the *Initator adapter* and transfers data to the `right` ledger with the *Responder adapter*;
- `right-to-left` the same, but with inverse order;
- `both` means that the two *Interledger instances* will be started in opposite directions to allow transfering data in both directions and that both *Initiator* and *Responder adapters* will be instantiated for both ledgers.

`left` and `right` are custom names and provide all the options needed to setup the ledgers. The available options depend on the `type` of the ledger, and more details of [Ethereum](/doc/adapter-eth.md), [Hyperledger Fabric](/doc/adapter-fabric.md), [Hyperledger Indy](/doc/adapter-indy.md) and [KSI](/doc/adapter-ksi.md) configuration options are available in their respective documents. Finally, *left* and *right* can also be the same, so it is possible to use Interledger to connect smart contracts on the same ledger, which can be used e.g. in testing; in that case, section 3 can be omitted.

#### Configuration Example for Ethereum

For ledger `type` =  `ethereum`, the required options are:

- **url:** the ethereum network url (localhost or with [Infura](https://infura.io/));
- **port:** if the url is localhost;
- **minter:** the contract minter (creator) address, which is also the account triggering the operations on a ledger;
- **contract:** the contract address;
- **contract_abi:** path to the file describing the contract ABI in JSON format.

As an example, there is the Interledger configuration file *config-file-name.cfg* for Ethereum, which defines two ledgers that are running locally on ports 7545 and 7546:

    [service]
    direction=both
    left=left
    right=right

    [left]
    type=ethereum
    url=http://localhost
    port=7545
    minter=0x63f7e0a227bCCD4701aB459b837446Ce61aaEb6D
    contract=0x50dc31410Cae2527b034233338B85872BE67EEe6
    contract_abi=solidity/contracts/GameToken.abi.json

    [right]
    type=ethereum
    url=http://localhost
    port=7546
    minter=0xc4C13639a867EfA9f863aF99A4c8d002E57198e0
    contract=0xba83df5f1DF4aB344240eC9F1E096790c88A216A
    contract_abi=solidity/contracts/GameToken.abi.json

For public Ethereum networks, external providers such as [Infura](https://infura.io/) can be utilised to avoid running a full Ethereum node. For external providers the additional option is:

- **private_key** the private key of the minter account used to sign the transaction;

Specifically, when using the Infura endpoints, please use the websocket version only so that the events emitted can be listened for properly. An example can be found in the `[infura]` part of the sample configuration `local-config.cfg`.

#### Configuration for multi-ledgers operation

For multi-ledgers mode, the Interledger component should be configured according to the following manner. 

1) `[service]`: defines the connected ledgers in a similar way for one-to-one connection, where the `direction` would be `multi` to indicate the multi-ledgers mode, and `left` and `rights` would be the connected ledgers. Note that since there is no bi-directional bridge for multi-ledgers situation, it is assumed that the single initiator would always be on the left, and the multiple responders are put at the right side. `threshold` indicates the minimum number of positive results required from the *Responders* to commit the transaction: if 'threshold' equals N (= the number of `right`s defined), this corresponds to an *all-N* scenario, while a lower value 0<*k*<*N* equals a *k-out-of-N* scenario.
    - `direction` = `multi`
    - `left` = *left*
    - `right` = *right1,right2,...*
    - `threshold`= *minimum-positives*

2) `[left]`: indicates the `type` of that ledger and lists its options. The options depend on the specific ledger.  
    - `type` = `ethereum` | `fabric` | `ksi` | ...
    - ...

3) `[right1], [right2]`: those sections follow the same way, to include the options for all the ledgers connected on the right side as the responders.
    - `type` = `ethereum` | `fabric` | `ksi` | ...
    - ...

A typical example of configuration file for multi-ledger connection can be found below (also available as [local-config-multi.cfg](/local-config-multi.cfg), which defines a 1-out-of-2 instance i.e. the transaction will succeed if at least one of the *Responders* succeeds:

```
[service]
direction=multi
left=left
right=right1,right2
threshold=1

[left]
type=ethereum
url=http://localhost
port=7545
minter=0xa1381e07D38Ddd2B82733407C43769dEd76d190a
contract=0x7f41e2562A34242423174eFa30204F77cd0E0e55
contract_abi=solidity/contracts/DataSender.abi.json

[right1]
type=ethereum
url=http://localhost
port=7546
minter=0xC57747a9682Cf7683a6B6161fdFbCd53b0695062
contract=0x2D429a3543a5fb6c3818f384EDd03b53a7434261
contract_abi=solidity/contracts/DataReceiver.abi.json

[right2]
type=ethereum
url=http://localhost
port=7547
minter=0x63f7e0a227bCCD4701aB459b837446Ce61aaEb6D
contract=0x50dc31410Cae2527b034233338B85872BE67EEe6
contract_abi=solidity/contracts/DataReceiver.abi.json
```

### Execution

For local testing, ensure that local ledger instances are running, and smart contracts are deployed to them (check [testing](#Testing) section for an example).

Then, run the following command:

```bash
python3 start_interledger.py config-file-name.cfg
```

where `config-file-name.cfg` is a configuration file for the setup of the interledger component, following the previously described `ini` format.

This script will create an *Interledger instance(s)* according to the configuration file and then call the `Interledger.run()` routine, which will listen to events coming from the connected ledger(s). The script can be interrupted with: `^C`.

There are multiple examples of utilising the Interledger component:

- [CLI demo app](/demo/cli) can be used to directly interact with the Interledger component.
- A simple example for [data transfer](/doc/example-data_transfer.rst) between two ledgers (both Ethereum or Hyperledger Fabric examples are included).
- Interledger component supports [storing hashes](/doc/adapter-ksi.md) to the [Guardtime KSI](https://guardtime.com/technology) blockchain using [Catena DB](https://tryout-catena.guardtime.net/swagger/) service.
- The [game asset transfer](/doc/example-game_asset_transfer.rst) example shows how a protocol for enforcing that in-game assets are only active in one of the connected ledgers at a time can be built on top of the Interledger.
- [Hash Time Locked Contracts (HTLCs)](/doc/example-HTLC.md) example describes how to use the Interledger to automate the asset exchange between two ledgers using HTLCs.


### Docker Images

Execute the script `docker-build.sh` to build a Docker image for the Interledger component. Configuration file can be provided to the image at runtime with the command `docker run -v /path/to/config.cfg:/var/interledger/local-config.cfg interledger`.

`Dockerfile` contains multiple build targets:
- **build**: only installs dependencies
- **interledger_compose**: in addition to the above, also compiles smart contracts; this target is used by the Docker Compose setup
- **run_demo**: runs Interledger command line demo
- **run (default)**: runs Inteledger component

**Docker Compose**

Docker Compose setup allows an easy usage of the Interledger [CLI demo](/demo/cli/README.md) by running `sh compose_start.sh`. Note that starting the whole setup will take some time, especially for the first time when all the necessary Docker images are built, so it is important to allow the startup script to shutdown gracefully.

The setup contains two Ganache CLI instances that act as local ledgers, the Interledger component, and the command line demo, see `docker-compose.yaml` for more details.

If there are any updates to the Interledger component, example smart contracts, `Dockerfile`, or `docker-compose.yaml`, run `docker-compose build` command to rebuild the containers.

***

## Testing

The `tests/` directory contains the scripts to test the software modules of the component, including unit tests, integration tests, and system tests, while the `solidity/test/` directory contains the tests for the smart contracts.

### Prerequisites for Testing

The easiest way to run the tests for the component is by using [Tox](https://tox.readthedocs.io/en/latest/), which will install all dependencies for testing and run all the tests. It is also possible to run the tests directly using pytest, which also allows running tests independently.

Install Tox:

```bash
pip install tox
```

Or install pytest and dependencies:

```bash
pip install pytest pytest-asyncio
```

Some of the tests assume that local Ethereum networks are running. Ganache CLI tool can be used for this:

```bash
npm install -g ganache-cli
```

To run component tests requiring local Ethereum networks, and to test example smart contracts, install Truffle:

```bash
cd solidity/
npm install
```

#### Environment

- [Truffle](https://www.trufflesuite.com/) to test the smart contracts (it includes the [Mocha](https://mochajs.org/) framework);
- The [pytest](https://docs.pytest.org/en/latest/getting-started.html) testing framework;
- The [pytest asyncio](https://github.com/pytest-dev/pytest-asyncio) library to test async co-routines.

### Running the Tests

First, local test networks need to be set up:

```bash
ganache-cli -p 7545 -b 1
ganache-cli -p 7546 -b 1
```

Here the block time is set to be one second as simulation of mining.

Afterwards, deploy the smart contracts to the local test networks:

```bash
make migrate-left
make migrate-right
```

Then, to test the component, run either:

```bash
tox
```

Or:

```bash
pytest --ignore=tests/system/test_ksi_responder.py --ignore=tests/system/test_interledger_ethereum_ksi.py --ignore=tests/system/test_timeout.py tests/
```

Read the [README](/tests/README.md) for pytest tests and test structure.

Note that testing the KSI support requires valid credentials for the Catena service. The tests can be run manually after adding credentials to `local-config.cfg`:

```bash
pytest tests/system/test_ksi_responder.py tests/system/test_interledger_ethereum_ksi.py
```

Note that testing timeout handling requires starting `ganache-cli` with `-b <blocking-time>` parameter:
```bash
ganache-cli -b 1 -p 7545
ganache-cli -b 1 -p 7546

pytest tests/system/test_timeout.py
```   

To test the smart contracts located in the `solidity` directory, shutdown `ganache-cli` instances (they will block the tests) and run the following (smart contracts are compiled automatically):

```bash
make test-contracts
```

### Evaluating the Results

When using Tox and Truffle, test results in JUnit format are stored in the `tests` directory. 
Files `python_test_results.xml` and `smart_contracts_test_results.xml` contain results for 
the Python and smart contracts' tests respectively.

### Test for multi-ledgers transaction

Integration tests for multi-ledgers mode have been included as well, with each step of the processing validated. It is not part of the default tests above, so to have to be run separately in the virtual envrionment with the following command:

```
python -m pytest --capture=sys tests/integration/test_interledger_multi.py
```

***

## Generating Documentation
A documentation file including the information provided by this readme and the docs for different modules and functions (both Python and Solidity) can be generated by using the [Sphinx](http://www.sphinx-doc.org/en/master/) tool. This section provides the commands to generate documentation in HTML and PDF formats.

### Requirements
- Install dependencies for generating documentation:
```bash
pip install 'sphinx<3.0.0' m2r sphinxcontrib-httpdomain sphinxcontrib-soliditydomain sphinxcontrib-seqdiag
```

- Solidity:
To generate code documentation for Solidity, install [soliditydomain](https://pypi.org/project/sphinxcontrib-soliditydomain/).

- PDF:
To generate documentation in PDF format, the `latexmk` package is required to be installed. Please follow the [instructions](http://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.latex.LaTeXBuilder). **warning! Does not work if Solidity files are included. Exlude them from the documentation if you want to generate PDF documentation.**

### Generation 

- For HTML docs
```bash
make html
```

- For PDF docs via LaTeX
```bash
make latexpdf
```

### Miscs

In case a new sphinx documentation project is created:
- select **yes** when the `sphinx quickstart` command asks for `autodoc`;
- include the lines below in `doc/conf.py`:

```python
import sys
sys.path.insert(0, os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc',
    'sphinxcontrib.soliditydomain',
    'sphinx.ext.coverage',
    ]

# autodoc lookup paths for solidity code
autodoc_lookup_path = '../solidity/contracts' # or any other path to smart-contracts
```

***

## Open Issues

- Each run of the module is done with empty data

This means that pending transactions from previous runs will not be considered and there is no recovery mechanism during re-start.

- Congestion of Ethereum transactions

If multiple transactions are invoked simultaneously, the (Ethereum) nonce of transactions generated by the component may be out of sync, thus making those invalid.

## Future Work

Some of the planned future improvements to the Interledger component include

- support for other ledger types, e.g. Quarum
- more complete implementation of [Decentralised Interledger (DIL)](/doc/decentralised-interledger.md)

***

## Release Notes

### 2020-12-17
#### Added
- support for [Hyperledger Indy](/doc/adapter-indy.md) as an Initiator
- initial implementation of [Decentralised Interledger (DIL)](/doc/decentralised-interledger.md)

### 2020-09-17
#### Added
- support multiple Responders in a single transaction (both all-N and k-out-of-N)

### 2020-08-07
#### Added
- Support for [Hyperledger Fabric](doc/adapter-fabric.md) ledger
- Example of using [Hash Time Locked Contracts (HTLCs)](doc/example-HTLC.md) with Interledger
- Support for passwords and PoA middleware for Ethereum
- [Measurement tests](/tests#performance-measurement) added for performance evaluation

#### Changed
- Performance improvements and optimizations for the Interledger core

#### Security
- Updated Truffle dependencies due to vulnerability in lodash

## Contact Information

**Contact**: Wu, Lei lei.1.wu@aalto.fi

**Contributors**: can be found in [authors](AUTHORS)



## License

This component is licensed under the Apache License 2.0.
