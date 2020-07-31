# Solidity
compile:
	cd solidity && npx truffle compile

migrate:
	cd solidity && npx truffle migrate --reset

migrate-both: migrate-left migrate-right

migrate-left:
	cd solidity && npx truffle migrate --reset --f 6 --to 6 --network left

migrate-right:
	cd solidity && npx truffle migrate --reset --f 6 --to 6 --network right

test-contracts:
	cd solidity && npx truffle test


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
