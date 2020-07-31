# Interledger Solidity smart contracts

## Installation

You can simply install dependencies with the command below:

```
$ npm install
```

NodeJS 5.0+ is recommended for the installation of Truffle.

## Compilation

You can compile the contracts with the following command:

```
$ npx truffle compile
```
It will create the required json files within the build directory.

You might need to remove the previous build directory beforehand:

```
$ rm -r build/
```

## Migration

Then you can run migration files using the below command:

```
$ npx truffle migrate
```

## Testing

Finally you can run tests using truffle internal network using the following command:

```
$ npx truffle test
```
Also, you can run tests using external networks (e.g ganache) using the following command:

```
$ npx truffle test --network ganache 
```

Please check the ``` truffle-config.js ``` file for more information about network setting. 