#!/bin/sh
# Waits until file 'config/local-config.cfg' exists, and runs
# the Interledger demo afterwards
config_file="config/local-config.cfg"

while [ ! -r "$config_file" ]
do
	sleep 1
done

python3 demo/cli/cli.py config/local-config.cfg
