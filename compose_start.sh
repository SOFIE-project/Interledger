#!/bin/sh
# Runs Compose setup for Interledger demo
# and removes shared volumes afterwards
docker-compose run --rm interledger_demo
docker-compose down -v
