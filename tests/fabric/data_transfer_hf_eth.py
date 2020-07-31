import os, sys
import asyncio
from datetime import datetime
from configparser import ConfigParser
from web3 import Web3

sys.path.append(os.path.realpath('.')) # assume running from project root
from start_interledger import parse_ethereum, parse_fabric
sys.path.append(os.path.realpath('./src'))
from data_transfer.interledger import Interledger
from data_transfer.ethereum import EthereumInitiator, EthereumResponder
from data_transfer.fabric import FabricInitiator, FabricResponder
from fabric_setup import channel_setup, data_sender_setup, data_receiver_setup, set_gopath


async def async_main():
    assert sys.argv[1] # configuration file, e.g. local-config-HF-ETH.cfg
    config_file = sys.argv[1]

    parser = ConfigParser()
    try:
      parser.read(config_file)
    except:
      print("Parsing configuration fails...")
      exit(-1)

    print("Parsing configuarations for HyperLedger Fabric network interaction...")
    # parse the configs for network at left side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'left1')
    net_profile = os.path.join('.', net_profile)

    # set up channel and get client
    cli = await channel_setup(net_profile, channel_name, org_name, user_name)

    # deploy chaincodes for data sender 
    await data_sender_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    # connect to initiator 1
    initiator1 = FabricInitiator(
      net_profile=net_profile,
      channel_name=channel_name,
      cc_name=cc_name,
      cc_version=cc_version,
      org_name=org_name,
      user_name=user_name,
      peer_name=peer_name)
    print("*** Have the Interledger initiator 1 connected ***")

    # parse the configs for network at right side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'right2')
    net_profile = os.path.join('.', net_profile)

    # deploy chaincodes for data receiver
    await data_receiver_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    # connect to responder 2
    responder2 = FabricResponder(
      net_profile=net_profile,
      channel_name=channel_name,
      cc_name=cc_name,
      cc_version=cc_version,
      org_name=org_name,
      user_name=user_name,
      peer_name=peer_name)
    print("*** Have the Interledger responder 2 connected ***")

    # parse ethereum network
    (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, "right1")

    # connect responder 1
    responder1 = EthereumResponder(minter, contract_address, contract_abi, url, port, private_key, password, poa)
    print("*** Have the Interledger responder 1 connected ***")

    # parse ethereum network
    (minter, contract_address, contract_abi, url, port, private_key, password, poa) = parse_ethereum(parser, "left2")

    # connect initiator 2
    initiator2 = EthereumInitiator(minter, contract_address, contract_abi, url, port, private_key, password, poa)
    print("*** Have the Interledger initiator 2 connected ***")

    # instantiate the Interledger components
    interledger1 = Interledger(initiator1, responder1)
    print("*** Have the interledger ready for HF --> ETH ***")

    interledger2 = Interledger(initiator2, responder2)
    print("*** Have the interledger ready for ETH --> HF ***")

    print('\n'*5)

    print("*********************************************")
    print("Data transfer: Hyperledger Fabric => Ethereum")
    print("*********************************************")

    task1 = asyncio.ensure_future(interledger1.run())

    set_gopath()
    await asyncio.sleep(5)

    org1_admin = cli.get_user(org_name='org1.example.com', name='Admin')

    # emit data
    print(f"--- emit data at: {datetime.now()} ---")

    args = ['0xabc123']
    # The response should be true if succeed
    response = await cli.chaincode_invoke(
        requestor=org1_admin,
        channel_name='mychannel',
        peers=['peer0.org1.example.com'],
        args=args,
        cc_name='data_sender',
        fcn='emitData',
        wait_for_event=True
    )

    await asyncio.sleep(3)
    interledger1.stop()
    await asyncio.sleep(1)
    task1.cancel()

    print('\n'*5)

    print("*********************************************")
    print("Data transfer: Ethereum => Hyperledger Fabric")
    print("*********************************************")

    task2 = asyncio.ensure_future(interledger2.run())

    await asyncio.sleep(5)

    # prepare data sender contract for emitting data
    w3 = Web3(Web3.HTTPProvider(url+":"+str(port)))
    data_sender = w3.eth.contract(abi=contract_abi, address=contract_address)

    tx_hash = data_sender.functions.emitData(b"0xdef456").transact({'from': minter})
    w3.eth.waitForTransactionReceipt(tx_hash)

    await asyncio.sleep(3)
    interledger2.stop()
    await asyncio.sleep(1)
    task2.cancel()

    exit(0)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == '__main__':
    main()