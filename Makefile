# Solidity
compile:
	cd truffle && npx truffle compile

migrate:
	cd truffle && npx truffle migrate --reset

migrate-8545:
	cd truffle && npx truffle migrate --reset --network ganache8545

migrate-7545:
	cd truffle && npx truffle migrate --reset --network ganache7545

test-contracts:
	cd truffle && npx truffle test


# Module testing
test-interledger:
	PYTHONPATH=$$PWD/src pytest tests/test_interledger.py -s

test-ethereum-ledger:
	PYTHONPATH=$$PWD/src pytest tests/test_ethereum_ledger.py -s

test-integration:
	PYTHONPATH=$$PWD/src pytest tests/test_integration.py -s


test-db-manager:
	PYTHONPATH=$$PWD/src pytest tests/test_db_manager.py -s

test-state-initiator-responder:
	PYTHONPATH=$$PWD/src pytest tests/test_state_initiator_responder.py -s

# Documentation
html:
	cd doc && make html

latexpdf:
	cd doc && make latexpdf
