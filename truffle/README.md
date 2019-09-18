# Solidity smart contracts

The smart contracts used for the Interledger component.
- **StateContract.sol**: The interface for the contract states in the asset transfer functionality;
- **GameToken.sol**: The ERC721 implementation for the asset transfer functionality: contract;

## Getting started
Getting started with truffle

### Test the contracts
    # Install tools
    npm install -g ganache-cli

    # Install truffle and contract dependencies
    npm install
    
### Local deployment demo with two Ethereum

Open two instances of Ganache (or geth) at port  `8545` and `7545` respectively. The `truffle-config.js` provides two networks to connect to such local ports: `ganache8545` and `ganache7545`. These two networks should be used for a testing / demo purpose.

The migration script deploys a new contract in the target network and modifies `../local-config.cfg` file with the address of the contract (`address`) and of the contract creator (`minter`) related to the target network.

For example:

    truffle migrate --reset --network ganache8545
    truffle migrate --reset --network ganache7545

In this way there is no need to modify by hand the configuration file, or to include the deployment in the starting script, when testing locally.

**Requires: npm ini module**: [ini](https://www.npmjs.com/package/ini)