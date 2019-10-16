# CLI application

How to use the CLI application:

1) ensure to have two ledgers working (locally);
2) ensure to have interledger running;

and execute

    python cli.py 'config.cfg'


Example (you might need 4 shell tabs):

```bash    
cd path/to/interledger-asset-transfer

# 1) Setup two ledgers
ganache -p 8545
ganache -p 7545
make migrate-8545
make migrate-7545

# 2) Start Interledger
python start_interledger.py local-config.cfg

# Start CLI app
python demo/cli/cli.py local-config.cfg
```

***
First of all, the CLI application prompts the user to choose the account to execute the transactions in both the ledgers. Then, the user can execute the following commands:

```python
mint <tokenId: int> <tokenURI: str> <assetName: str> # mint a token
transfer_out <direction> <tokenId: int> # transfer a token out from the ledger <directions>
state_of <tokenId> # get state of the token
help # show this list
quit # quit CLI app
```
where available **< direction >** directions are:

    left
    right 

The contract used by the cli application is [this ERC721](../../truffle/contracts/GameToken.sol) implementation. An example of `mint` input can be: `tokenId=`123, `assetURI=`/toys/, `assetName=`ball123.

> **_NOTE:_**  [this ERC721](../../truffle/contracts/GameToken.sol) token contract follows the requirements of the SOFIE Gaming Pilot. In this contract the term `tokenId` corresponds to the ERC token id specification AND to the `assetId` of the interledger protocol.

> **_NOTE-2:_**  when created a token (asset) is by deafult in NOTHERE state. For simulation purpose, the `mint` command will create two identical tokens in both the ledgers AND will set the token in ledger `right` to HERE. 

Example of workflow:
```python
# Choose account from list in ledger left
)> 3
# Choose account from list in ledger right
)> 3

# mint ERC token
)> mint 123 /toys/ ball123
# get state of token
)> state_of 123
## *Here* in ledger right; *NotHere* in ledger left

# transfer the token 123 from ledger right to ledger left
)> transfer_out right 123
)> state_of 123
## *NotHere* in ledger right; *Here* in ledger left
```
