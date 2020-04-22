# Solidity smart contracts

The smart contracts in this repositories are:
- **AssetTransferInterface.sol**: The interface for the contract states in the asset transfer protocol of the Interledger component;
- **GameToken.sol**: A ERC721 token implementing the interface above for the asset transfer protocol. Note, `tokenId` corresponds to the ERC token id specification AND to the `assetId` of the interledger protocol. **In other words, the ERC implementation uses the token ids as ids for the IL asset transfer protocol.** _This contract follows the specifications of the SOFIE gaming pilot. In that case the id of the token (uint) is different from the id of the asset (string or bytes32), but both are unique._


## Getting started

If you are not familiar with the Truffle framework, plase [see this page](https://www.trufflesuite.com/truffle).

Getting started with truffle

```bash
# Install tools
npm install -g ganache-cli

# Install truffle *locally* and dependencies
npm install
```

### Test the contracts
    truffle test

or, using the Makefile:

    cd ..
    make test-contracts

### DEMO: Local deployment with two Ethereum instances

**Requires: npm ini module**: [ini](https://www.npmjs.com/package/ini)

> **Use case** You want to deploy the contracts in one or two Ethereum **local** networks. 

1 - Open two instances of Ganache at port  `8545` and `7545` respectively.

    ganache-cli -p 8545
    ganache-cli -p 7545

The `truffle-config.js` provides two local networks targets, `ganache8545` and `ganache7545`, to connect the migration script to such ports. [See Truffle's page](https://www.trufflesuite.com/docs/truffle/reference/configuration#networks) for more info.

During the [migration](./migrations/1_initial_migration.js), [the ERC721 token](./contracts/GameToken.sol) will be deployed in the target network. 

2 - Execute migrations:

    truffle migrate --reset --network ganache8545
    truffle migrate --reset --network ganache7545

or, using the Makefile:

    cd ..
    make migrate-8545
    make migrate-7545

will deploy a GameToken contract in each network.

Moreover, the migration script modifies `../local-config.cfg` configuration file with the address of the contract (`address`) and of the contract creator (`minter`) related to the target network. These fields will be used by the [interledger execution script](../start_interledger.py) and the [CLI demo application](../demo/cli/cli.py).