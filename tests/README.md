# Running tests

Testing framework: `pytest`

Include pytest option `-s` to output the test prints; `-v` to list all the test methods.
To run following tests, `pytest` and `pytest-asyncio` need be installed.
    
    pip install pytest pytest-asyncio

## Unit tests

The current modules have a lot of dependencies, so unit tests are very small, mainly concerning initializations.

    pytest tests/unit/
    pytest tests/unit/test_interledger.py

## Integration tests

This test set is richer than unit test set. In this set there are most of the methods provided by the modules, which can be tested without any other external resource / service.

    pytest tests/integration/
    pytest tests/integration/test_interledger.py

## System tests

This test set is not self-dependent. The modules interacting with ethereum need a local ethereum instance running. These examples use ganache-cli.

**Testing Ethereum Initiator and Responder: One instance running on port 7545**

    ganache-cli -p 7545
    pytest tests/system/test_ethereuminitiator.py
    pytest tests/system/test_ethereumresponder.py

These tests examine the correctness of different modules of EthereumInitiator and EthereumResponder classes. 

**Testing Ethereum Initiator and Responder:**
These tests examine the correctness of KsiResponder's functionalities. 
    
    pytest tests/system/test_ethereumresponder.py
    pytest tests/system/test_interledger_ethereum_ksi.py

> **NOTE** The credintial for ksi should be specified in local-config file before running following tests.

**Testing timeouts**

To run these tests run ganache-cli **without** auto-mining: add the flag `-b 1` which sets up a mining time of 1 second. 

    ganache-cli -p 8545 -b 1
    pytest tests/system/test_timeout_.py

This test checks behavior of different modules of EthereumInitiator and EthereumResponder classes under timeout condition.
> **NOTE** Having the -b option always activated will slow down all the other tests.

**Testing Interledger: Two instances running on ports 7545 and 7546**

    ganache-cli -p 7545
    ganache-cli -p 7546
    pytest tests/system/
    pytest tests/system/test_interledger_ethereum.py
This test examine both way communication between two different ledgers which is controlled by the interledger component.

## Performance measurements

To evaluate the cost and performance in throughput, the following measurements can be carried out.

First set up the test networks respectively, setting a block time with the `-b` flag.

    ganache-cli -p 7545 -b 1 
    ganache-cli -p 7546 -b 1

The next step is to deploy the sample `GameToken` smart contract on the test networks above, respectively.

    make migrate-left
    make migrate-right

This way, the measurement of total gas usage and elapsed time of complete processes of the sample GameToken transfer with and without the Interledger component can be extracted by running the following tests.

    pytest tests/system/test_measurement_interledger_ethereum.py
    pytest tests/system/test_measurement_e2e_ethereum.py

Note that the comparison measurement without using the component is conducted by the following. In this case, the `GameTokenWithoutInterledger` smart contract should be used on ledgers of both sides.

    cd solidity
    truffle migrate --reset --f 7 --network left
    truffle migrate --reset --f 7 --network right

Above steps are to be taken to deploy that smart contract for comparision purposes.

Similarly, the performance when processing simultaneous incoming transfers can be tested and analyzed by running the following two tests respectively, after the same set up above. 

    pytest tests/system/ethereum_with_interledger_multiple.py
    pytest tests/system/ethereum_without_interledger_multiple.py

Note the first one above is for simultaneous `GameToken` smart contract transfers with interledger, while the second one is for the comparison without the component, where `GameTokenWithoutInterledger` smart contract should be deployed and used. 


## Known issues
- integration/test_interledger.py, after running `interledger`, interledger.run(), the test needs `await asyncio.sleep()` before emitting event, otherwise coroutines block;
