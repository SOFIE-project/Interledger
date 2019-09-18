# Running Interledger tests

Testing framework: `pytest`

### Interledger unit testing

**Setup requirements:** None

    cd ..
    PYTHONPATH=$PWD/src pytest tests/test_interledger.py -s

### Ethereum ledger unit testing

**Setup requirements:** Ethereum local network (e.g. Ganache): `port: 8545`

    cd ..
    PYTHONPATH=$PWD/src pytest tests/test_ethereum_ledger.py -s

### Integration testing

**Setup requirements:** 2x Ethereum local networks (e.g. Ganache): `port: 8545` and `port: 7545`

    cd ..
    PYTHONPATH=$PWD/src pytest tests/test_integration.py -s

## Known issues
- importing `web3` raises a warning in pytest environment;
- integration test, after running `interledger` needs `await asyncio.sleep()` before emitting event, otherwise coroutines block;

## TODO
- [ ] Structure the code better into packages, add a `setup.py` and avoid to modify PYTHONPATH at command line;
- [ ] Figure out how to synchronize better interldeger functions;
- [ ] Provide better tests?