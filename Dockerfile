# build with "export DOCKER_BUILDKIT=1"
FROM python:3.6 AS build

RUN apt-get update && \
	apt-get -y install gcc g++ linux-headers-amd64 libffi-dev libgnutls28-dev && \
	rm -rf /var/lib/apt/lists/*
COPY ./ /var/interledger/
WORKDIR /var/interledger
RUN python3 setup.py develop


# For Docker compose setup, this target also compiles smart contracts
# custom CMD should migrate smart contracts and start the Interledger
FROM build AS interledger_compose

RUN apt-get update && \
    apt-get -y install npm && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /var/interledger/solidity
RUN npm install -g npm@latest
RUN npm install
RUN npx truffle compile
WORKDIR /var/interledger/


# Run Interledger CLI demo
FROM build AS run_demo
CMD [ "python3", "demo/cli/cli.py", "local-config.cfg" ]


# Run Interledger
FROM build AS run
CMD [ "python3", "start_interledger.py", "local-config.cfg" ]
