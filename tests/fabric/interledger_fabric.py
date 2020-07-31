import os, sys
import asyncio
from datetime import datetime
from configparser import ConfigParser

sys.path.append(os.path.realpath('.')) # assume running from project root
from start_interledger import parse_fabric
sys.path.append(os.path.realpath('./src'))
from data_transfer.interledger import Interledger
from data_transfer.fabric import FabricInitiator, FabricResponder
from fabric_setup import fabric_setup, set_gopath


async def async_main():
    assert sys.argv[1] # ensures a configuration file
    config_file = sys.argv[1]

    parser = ConfigParser()
    try:
      parser.read(config_file)
    except:
      print("Parsing configuration fails...")
      exit(-1)

    print("Parsing configuarations for HyperLedger Fabric network interaction...")

    # parse the configs for network at left side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'left')

    net_profile = os.path.join('.', net_profile)

    # have the data sender and receiver deployed
    cli = await fabric_setup()

    # connect to initiator
    initiator = FabricInitiator(
      net_profile=net_profile,
      channel_name=channel_name,
      cc_name=cc_name,
      cc_version=cc_version,
      org_name=org_name,
      user_name=user_name,
      peer_name=peer_name)

    print("*** Have the Interledger initiator connected ***")

    # parse the configs for network at right side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'right')

    # connect to responder
    responder = FabricResponder(
      net_profile=net_profile,
      channel_name=channel_name,
      cc_name=cc_name,
      cc_version=cc_version,
      org_name=org_name,
      user_name=user_name,
      peer_name=peer_name)

    print("*** Have the Interledger initiator connected ***")

    # instantiate the Interledger component
    interledger = Interledger(initiator, responder)

    # get the interledger running
    task = asyncio.ensure_future(interledger.run())

    
    set_gopath()
    await asyncio.sleep(7)

    org1_admin = cli.get_user(org_name='org1.example.com', name='Admin')

    # emit data
    print("********************************")
    print(f"emit data at: {datetime.now()}")
    print("********************************")

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

    await asyncio.sleep(5)
    interledger.stop()
    await asyncio.sleep(5)

    exit(0)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == '__main__':
    main()