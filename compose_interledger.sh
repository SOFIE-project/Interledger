#!/bin/sh
# Used inside Docker Compose environment
# deploys smart contracts and runs Interledger afterwards


# TODO: wait until both Ganache instances are running
# ....

# use different configuration file for Compose environment
cp compose.cfg local-config.cfg

# deploy smart contracts, this will update configuration file
#apk add npm
#npm install
cd solidity/
npx truffle migrate --reset --network compose_left
npx truffle migrate --reset --network compose_right
cd ..

# copy the updated configuration file to shared directory
cp local-config.cfg config/

# start Interledger
python3 start_interledger.py local-config.cfg
