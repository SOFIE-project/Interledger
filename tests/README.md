# Running tests

Testing framework: `pytest`

Include pytest option `-s` to output the test prints; `-v` to list all the test methods.

## Unit tests

The current modules have a lot of dependencies, so unit tests are very small, mainly concerning initializations.

    pytest tests/unit/
    pytest tests/unit/test_interledger.py

## Integration tests

This test set is more rich than unit test set. In this set there are most most of the methods provided by the modules which can be tested without any other external resource / service.

    pytest tests/integration/
    pytest tests/integration/test_interledger.py

## System tests

This test set is not self-dependent. The modules interacting with ethereum need a local ethereum instance running. These examples use ganache-cli.

**One instance running on port 8545**

    ganache-cli -p 8545
    pytest tests/system/test_ethereuminitiator.py
    pytest tests/system/test_ethereumresponder.py

**Two instances running on ports 8545 and 7545**

    ganache-cli -p 8545
    ganache-cli -p 7545
    pytest tests/system/
    pytest tests/system/test_interledger.py

## Known issues
- importing `web3` raises a warning in pytest environment;
- integration test, after running `interledger` needs `await asyncio.sleep()` before emitting event, otherwise coroutines block;
