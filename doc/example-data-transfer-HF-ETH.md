# Example of Hyperledger Fabric to Ethereum Data Transfer

## Networks set up

First the Hyperledger Fabric and Ethereum networks on both sides of the Interledger component should be set up, upon which the chaincode and/or smart contract for data sender and receiver can be deployed.

For Hyperledger Fabric, the similar procedure in [Adapter Fabric](./adapter-fabric.md#Network-set-up) should be followed. And in this tests the deployment of chaincodes for both data sender and receiver will be covered by the [test script](../tests/fabric/data_transfer_hf_eth.py). Note that the chaincode deployment may take a while to settle.

For Ethereum side, private test networks can be easily set up as follows.

```
ganache-cli -p 7545 -b 1
ganache-cli -p 7546 -b 1
```

## Deployment

The smart contracts for data sender and receiver could be deployed as follows.

```
truffle migrate --reset --f 2 --to 2 --network left
truffle migrate --reset --f 3 --to 3 --network right
```

After the migrations settle, the corresponding configuration file `local-config-HF-ETH.cfg` should be updated for correspnding sections, like `right1` for the data receiver and `left2` for data sender.

## Execution

With the above set up and deployments, it is ready to test for data transfers between:

1. Hyperledger Fabric (left1) to Ethereum (right1) networks
2. Ethereuem (left2) to Hyperledger Fabric networks

with the following commands.

```
export PATH=$PATH:$PWD/fabric/bin
python tests/fabric/data_transfer_hf_eth.py local-config-HF-ETH.cfg 
```

The actions of data payload being transferred between the two types of distributed ledgers can be observed from the standard outputs.
