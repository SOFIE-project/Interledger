# SOFIE Interledger component

**Table of contents:**

- [Description](#description)
    - [Architecture Overview](#architecture-overview)
    - [Main Concepts](#main-concepts)
    - [Relation with SOFIE](#relation-with-sofie)
    - [Key Technologies](#key-technologies)

- [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Interledger Configuration](#interledger-configuration)
    - [Execution](#execution)

- [Testing](#testing)
    - [Environment](#environment)
    - [Running the tests](#running-the-tests)
    - [Evaluating the results](#evaluating-the-results)

- [Integration](#integration)
- [Deployment](#deployment)
- [Open and Known Issues](#known-and-open-issues)
- [Contact Info](#contact-info)

- [Generating documentation](#generating-documentation)


## Description

The SOFIE Interledger component implements a protocol to bridge two ledgers (A, B). If a particular event has been emitted in ledger A, then the Interledger component will catch that event and will perform some operation in ledger B.

In particular, the Interledger component currently supports the “transfer” of an asset from ledger A to ledger B, and vice versa.


### Architecture Overview

**Premise:** to avoid confusion, with **Interledger component** we refer to the set of smart contracts and modules, meanwhile with **Interledger module** to the class named Interledger.

The asset transfer functionality of the Interledger component is implemented with a state machine. Each asset has a "state" indicating its presence or absence in a ledger. The state machine is implemented as follows:

- The state information is stored in **smart contracts**. A smart contract stores the state of the asset in the ledger it has been deployed in and exposes the methods to switch between states;
- The transition between states is implemented by the **software modules**. The main  modules are the three listed below:

    - **Initiator:** is responsible to catch the events from a ledger and to finalize or abort the protocol depending on the result received from the Responder;
    - **Responder:** receives transfer requests from the Initiator and is responsible to start the transfer to the other ledger;
    - **Interledger:** creates a bridge from a ledger A to a ledger B by instantiating a Initiator listening for events coming from ledger A and executing transactions to ledger B by instantiating a Responder. To handle transfers from ledger B to ledger A, instantiate a second Interledger with Initiator connected to ledger B and Responder connected to ledger A.

The figure below shows how these modules interact with each other.

Currently the Interledger component supports Ethereum. In order for the component to support another ledger, Initator and Responder classes must be extended to be able to read and write from/to that particular ledger, along with the necessary smart contracts.

The figure below shows an implementation of the Initiator and Responder connected to the Ethereum network.

![Interledger](/imgs/Struct.png)

### Relation with SOFIE

The interledger component is standalone, it may be used by other SOFIE components and applications as necessary.

### Main Concepts

The design of the architecture is driven by the asset transfer scenario of the SOFIE Gaming Pilot. For more details please check [this readme](/src/sofie_asset_transfer/README.md), located in the src/sofie_asset_transfer directory.


### Key Technologies

The software modules are implemented in **Python**.
Currently the component supports the Ethereum ledger and thus **Solidity** smart contracts.

***

## Usage

The `src/sofie_asset_transfer` directory contains the code implementing the software modules.
The `truffle/contracts` contains the smart contracts used by the component.

### Prerequisites

Software modules: **Python 3.6**.

Smart contracts: **Solidity 0.5**.

[Truffle framework](https://www.trufflesuite.com/) project and other NodeJs modules: **node package manager, npm**.

To implement the Ethereum version of both Initiator and Responder, the python [web3 library](https://web3py.readthedocs.io/en/stable/web3.eth.html) is needed.

### Installation

Install Truffle (which includes the Solidity compiler) and [OpenZeppelin](https://github.com/openzeppelin/openzeppelin-contracts) smart contract dependencies.

```bash
cd truffle/
npm install
```

Install module requirements.

```bash
virtualenv -p python3 my-env
source my-env/bin/activate
python3 setup.py develop # Install project dependencies locally
python3 setup.py test # Install test dependencies
```

### Interledger configuration

The configuration file, following the `ini` format, has three main sections:

1) `[service]`: defines the connected ledgers, `left` and `right`, and the `direction` of the data transer;
    - `direction` = `both` | `left-to-right` | `right-to-left`
    - `left` = *ledger_left*
    - `right` = *ledger_right*

2) `[ledger_left]`: indicates the `type` of that ledger and lists its options. The options depend on the specific ledger.  
    - `type` = `ethereum` | ...
    - ...

3) `[ledger_right]`: same as above.
    - `type` = `ethereum` | ...
    - ...

The `direction` can have three values:
- `left-to-right` means that interledger listens for events upcoming from the left ledger `ledger_left` and transfers data to the right ledger `ledger_right`. The interledger component has an `Initiator` adapter for the left ledger and a `Responder` adapter for the right ledger;
- `right-to-left` the same, but with inverse order;
- `both` means the interledger can transfer an asset both ways. Both `Initiator` and `Responder` adapters will be instatiated for both ledgers.

`ledger_left` and `ledger_right` are custom names and provide all the options needed to setup the ledgers. The options depend on the `type` of the ledger. Finally, *ledger_left* and *ledger_right* can also be the same: in that case, no 3) section is needed.


**Example of configuration to a single Ethereum ledger**

For `type` =  `ethereum`, the required options are:

- **url:** the ethereum network url (localhost or with [infura](https://infura.io/));
- **port:** if the url is localhost;
- **minter:** the contract minter (creator) address;
- **contract:** the contract address.

Example of the Interledger configuration file:

    [service]
    direction=both
    left=ganache
    right=ganache

    [ganache]
    type=ethereum
    url=http://localhost
    port=8545
    minter=0x63f7e0a227bCCD4701aB459b837446Ce61aaEb6D
    contract=0x50dc31410Cae2527b034233338B85872BE67EEe6

### Execution

Run the following command:

    python3 start_interledger.py config-file-name.cfg

Where `config-file-name.cfg` is a configuration file for the setup of the interledger component, following the previously described `ini` format.

This script will create a proper Interledger component instance according to the input configuration file and call the `Interledger.run()` routine which will listen to events coming from the connected ledger(s). The script can be interrupted with: `^C`.

**Example of Interledger running locally**

This example uses two different ganache networks (both running in localhost, but listening on two different ports). For the asset, this example uses ERC721-compatible [token](/truffle/contracts/GameToken.sol) contract, which also implements the state interface provided by [this contract](/truffle/contracts/StateContract.sol).

From now on, we use [ganache-cli](https://github.com/trufflesuite/ganache-cli) as local Ethereum instance. The option ``-p`` identifies the port.

To setup, first run two ``ganache-cli`` and then migrate the contracts by help of the Makefile. Finally, run the interledger.

```bash
ganache-cli -p 8545
ganache-cli -p 7545

make migrate-8545
make migrate-7545

python3 start_interledger.py local-config.cfg
```

Since every run of `ganache-cli` generates different addresses, migration targets (`migrate-8545` and `migrate-7545`) deploy the contracts in their target networks (localhost:8545 and localhost:7545 respectively), and then modify the `local-config.cfg` file with the account and contract addresses.

At this point is possible to create tokens in the target networks. When a  `transferOut()` function (see [this readme](/src/sofie_asset_transfer/README.md)) will be called on a asset, the Interledger component will transfer that asset to the other network.

This can be done via scripts using truffle:
```bash
cd truffle
truffle execute your-script.js --network network-name
```

or interactively using truffle console:
```bash
cd truffle
truffle console --network network-name
(network-name)> ...
```

***

## Testing

The `test/` directory contains the scripts to unit test the software modules of the component.
The `truffle/test/` directory contains the scripts to unit test the smart contracts.

### Environment

- [Truffle](https://www.trufflesuite.com/) to test the smart contracts (it has the [Mocha](https://mochajs.org/) framework embedded);
- The [pytest](https://docs.pytest.org/en/latest/getting-started.html) testing framework;
- The [pytest asyncio](https://github.com/pytest-dev/pytest-asyncio) library to test async co-routines.

### Running the tests

Read the README in [the testing directory](/tests/README.md) for pytest tests and test structure.

To test the smart contracts located in `truffle` directory (it compiles them automatically):
```bash
# Test the contracts
make test-contracts
```

<!-- Similarly, to test the modules Ethereum Initiator and Responder with a Mock Interledger:
```bash
# Compile contracts
make compile
# Test the Ethereum initiator and responder
ganache-cli -p 8545
make test-ethereum-ledger
```

To test both Ethereum Initiator, Responder and Interledger run two local Ethereum instances and execute the test as follows:
```bash
# Compile contracts
make compile
# Test the Ethereum initiator and responder with interledger
ganache-cli -p 8545
ganache-cli -p 7545
make test-integration
``` -->

### Evaluating the results

At the current state of the implementation, no particular results are logged after the tests.

***

## Integration

At the current state of the implementation, there is no continuous integration support.

## Deployment 

At the current state of the implementation, there is no continuous deployment support.

## Known and Open issues

Integration and Deployment are not yet supported. 

Moreover, the limitations of the Interledger module are:

- No closing procedure after a stop:
    - No resource cleanup;
- Each run of the module is done with empty data: this means that pending transactions from previous runs will not be considered:
    - There is no recovery mechanism during re-start;
- No automatic error detection:
    - If a transaction fails at any step, the modules does not support any retry mechanism. Therefore a transfer can be left incomplete, breaking the invariant;
    - The abort step should be done manually by interacting directly with the smart contract;
    
***

## Generating documentation

A documentation file including the information provided by the current readme, [asset transfer protocol readme](/src/sofie_asset_transfer/README.md), and the functions (both Python and Solidity) can be generated by using the [Sphinx](http://www.sphinx-doc.org/en/master/) tool. This section provides the commands to generate documentation in HTML and PDF formats.

**Requirements**

- To generate code documentation for Solidity, install [soliditydomain](https://pypi.org/project/sphinxcontrib-soliditydomain/).
- To generate documentation in PDF format, follow [these instructions](http://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.latex.LaTeXBuilder). **warning! Does not work if Solidity files are included. Exlude them from the documentation if you want to generate PDF documentation.**

**Generate HTML documentation:**

```bash
make html
```

**Generate PDF documentation via LaTeX:**

```bash
make latexpdf
```

**In case a new sphinx documentation project is created:**

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
autodoc_lookup_path = '../truffle/contracts' # or any other path to smart-contracts
```

***

## Contact Info

andrea.lisi@aalto.fi

After the 1st of November 2019, send email to:
andrealisi.12lj@gmail.com with subject [SOFIE] or [SOFIE Interleger].

***
## License

This component is licensed under the Apache License 2.0.
