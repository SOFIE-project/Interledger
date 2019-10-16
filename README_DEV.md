# Developing Interledger

## Go through the repository

The current directory contains the project of the Interledger component for SOFIE.

- The `src` directory contains the component source code. 
    - The `sofie_asset_transfer` directory contains the python code implementing the asset transfer protocol for SOFIE's use cases. The protocol is based on a state machine and is described by the README in that folder.
        - Currenlty only Ethereum is supported. To integrate another ledger is required to implement the Initiator and Responder interfaces in `interfaces.py`. For example, the `Initiator.get_transfers()` functions should implement an event listener to catch events fired by the ledger, meanwhile the other functions should call the smart contract functions as required by the protocol: transferOut(), commit(), abort() and accept().
    - The `StateInitiator` and `StateResponder` are subclasses storing the new states of transfers in a DB for future recovery.

    - The `db_manager` directory contains a simple wrapper of a sql_alchemy object providing the CRUD methods to the asset transfer protocol modules.

- The `tests` directory contains the tests for the Python modules, divided into:
    - `unit`, test the methods of the modules not depending on external objects;
    - `integration`, test the methods that interact with other objects. Such object are mocked;
    - `system`, test the modules with a running instance of Ethereum (Ganache).

- The `truffle` directory contains a truffle project to implement the smart contracts. The contracts available are `AssetTransferInterface` providing an interface of the protocol for Ethereum, and `GameToken`, an example of ERC721 contract implementing the aforementioned interface.

- The `doc` folder contains restructured text documentation for a sphinx project. _Last update: beginning of September 2019, demo in Terni._

## Start working with it

Read the README. But here a guideline:

- First of all you might want to install everything.
    - Start with the `truffle` directory. Go and install the `npm` dependencies with `npm install`. **It requires nodejs and npm**
    - Type `truffle test` to see if truffle has been installed correctly. The tests should pass even without running ganache-cli and `truffle-migrate`.
    - If truffle is correctly installed and tests works, create a `virtualenv` in the main project folder and `activate` it.
    - Install the requirements with `python setup.py develop` and `python setup.py test`.
    - Test if the installation went well by running python tests. Type `pytest tests/unit` and `pytest tests/integration`: they do not rely on external resources.
- If everything goes well, you can run the component. The script `start_interledger` needs as command line argument a configuration file in .ini format: it reads such file and sets up a one or two-sided Interledger: one sided Interledger means that an asset can be transfered only one way: you can imagine the trasfer going "from the ledger referenced by the Initiator to the ledger referenced by the Responder"; two sided Interledger creates underneats two instances of `sofie_asset_transfer.interledger.Interledger`, each one with its pair of Initiator and Responder. 
- You can play with the IL protocol with the CLI application. You need to open 4 tabs:
    - Tab 1: run `ganache-cli -p 8545`;
    - Tab 2: run `ganache-cli -p 7545`;
    - Tab 3: run `make migrate-8545`, `make-migrate-7545` and `python start_interledger.py local-config.cfg`: now IL should actively run in loop (it won't print anything apart from a single line to notify that it is running);
    - Tab 4: run `python demo/cli/cli.py local-config.cfg` and do as suggested in demo/cli/README. Try to transfer_out an asset and check its state if changes.
    - > The commands `make migrate-*` automatically updates the `local-config.cfg` with the user and contract addresses after the migration. Is important to run interledger and CLI app after the migration, otherwise the scripts may not find the right contract or no contract at all.

## What's next

- The `sofie_asset_transfer.interledger.Interledger` class:
    - [ ] The class uses two lists, `transfers` and `transfers_sent`, which iterates over continuosly, without never cleaning them when a transfer is finally processed (it has its state set to PROCESSED).
    - [ ] There is no closing procedure in case Interledger needs to be stopped (e.g. finish to process the remaining transfers or ignore them).
    - [ ] Since the transactions with a ledger may take a while (e.g. Ethereum avg transaction time is 13s), there is no timeout exception if the transaction takes to long to be processed.
    - [ ] No counter-measure is taken in case of network failure: Interledger may simply stop working with an Exception.
    - [ ] No rollback method in case one of the above errors occurr. For example, if the `commit()` function is somehow impossible due to external factors, the asset will end up in a state which is not possible to roll back, but only commit (sooner or later). This **may or may not** need to define new methods in the interface and the protocol to handle this rollback. Needs more investigation.

- The `sofie_asset_transfer.interfaces` module:
    - [ ] An implementation of Initiator and Responder able to interact with another ledger. In SOFIE, Hyperledger Fabric (HF) is a ledger that is going to be used.
    - [ ] Find a different return value from True / False, if needed.

- The `sofie_asset_transfer.db_manager` module:
    - [ ] Design a better DB composition if needed: at the moment there are two un-related tables.
    - [ ] Improve the `DBManager` class or provide another one, if needed.

- Smart contracts:
    - [ ] Alongside the implemetation of Initiator and Responder for a different ledger, the related smart contract providing the protocol methods needs to be implemented as well (e.g. Chaincode for HF).

- User interaction / demo:
    - [ ] Extend CLI application;
    - [ ] Provide GUI application;


#### Do not forget to update the test suite by providing tests (unit, integration and system) for any new feature.
