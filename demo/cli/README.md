# CLI application

Interledger CLI applications provides an easy way to test the Interledger functionality. It can be run as a part of Docker Compose setup as described [here](../../README.md#docker-images) or manually. Below is a description how to run the CLI application manually:

1) ensure to have two ledgers working (locally);
2) ensure to have Interledger component running;

and execute

    python cli.py 'config.cfg'


For example (you need 4 shell tabs):

```bash    
cd path/to/interledger-asset-transfer

# 1) Setup two ledgers
ganache -p 7545
ganache -p 7546
make migrate-left
make migrate-right

# 2) Start Interledger
python start_interledger.py local-config.cfg

# Start CLI app
python demo/cli/cli.py local-config.cfg
```


***
The CLI application connects to both of the ledgers. Then, the user can execute the following commands:

```python
mint <tokenId: int> <tokenURI: str> <assetName: str> # mint a token
transfer_out <ledger: str> <tokenId: int> # transfer a token out from the ledger <ledger>
state_of <tokenId: int> # get state of the token
example_run # runs an example consisting of: minting tokens, activing a token, and transferring the token out
help # show this list
quit # quit the CLI application
```
where available **< ledger >** ledgers are:

    left
    right 

The contract used by the cli application is [this ERC721](../../solidity/contracts/GameToken.sol) implementation. An example of `mint` input can be: `tokenId=`123, `assetURI=`/toys/, `assetName=`ball123.

> **_NOTE:_**  [this ERC721](../../solidity/contracts/GameToken.sol) token contract follows the requirements of the SOFIE Gaming Pilot. In this contract the term `tokenId` corresponds to the ERC token id specification AND to the `id` of the interledger protocol.

> **_NOTE-2:_**  when created a token (asset) is by deafult in NOTHERE state. For simulation purpose, the `mint` command will create two identical tokens in both the ledgers AND will set the token in ledger `left` to HERE. 

Example of workflow:
```python
# mint the token
)> mint 123 /toys/ ball123
# get state of token
)> state_of 123
## *Here* in ledger left; *NotHere* in ledger right

# transfer the token 123 from ledger left to ledger right
)> transfer_out left 123
)> state_of 123
## *NotHere* in ledger left; *Here* in ledger right
```
