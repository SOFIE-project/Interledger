# build with "export DOCKER_BUILDKIT=1"
FROM python:3.6-alpine AS build

RUN apk add --no-cache gcc g++ musl-dev linux-headers libffi-dev openssl-dev
COPY ./ /var/interledger/
WORKDIR /var/interledger
RUN python3 setup.py develop


# For Docker compose setup, this target also compiles smart contracts
# custom CMD should migrate smart contracts and start the Interledger
FROM build AS interledger_compose

RUN apk --no-cache add npm
WORKDIR /var/interledger/solidity
RUN npm install
RUN npx truffle compile
WORKDIR /var/interledger/


# Run Interledger CLI demo
FROM build AS run_demo
CMD [ "python3", "demo/cli/cli.py", "local-config.cfg" ]


# Run Interledger
FROM build AS run
CMD [ "python3", "start_interledger.py", "local-config.cfg" ]
