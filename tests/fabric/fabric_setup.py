import os, sys
import asyncio
from configparser import ConfigParser
from datetime import datetime
from hfc.fabric import Client

sys.path.append(os.path.realpath('.'))

from start_interledger import parse_fabric


# for network setup and chaincode deployment
CONFIG_YAML_PATH = './fabric/fixtures/e2e_cli/'
CHAINCODE_PATH = './fabric/chaincode'


async def channel_setup(net_profile, channel_name, org_name, user_name):
    """Set up the client, creata channel and join peers into it
    :param net_profile: the network profile, the rest uses static settings other than parameters

    :returns: the client for further interaction
    """
    cli = Client(net_profile=net_profile)

    print(cli.organizations) # orgs in the network
    print(cli.peers) # peers in the network
    print(cli.orderers) # orderers in the network
    print(cli.CAs) # ca nodes in the network

    # get the admin user from local path
    org1_admin = cli.get_user(org_name=org_name, name=user_name)

    orderer = list(cli.orderers)[0] # assumes the first to choose

    # Create a New Channel, the response should be true if succeed
    response = await cli.channel_create(
        orderer=orderer, 
        channel_name=channel_name,
        requestor=org1_admin,
        config_yaml=CONFIG_YAML_PATH,
        channel_profile='TwoOrgsChannel'
    )
    if response:
        print("Create channel successful")
        print("Create channel response:", response)
    else:
        print("Create channel failed")
        print(response)
        exit(-1)

    # Join Peers into Channel, the response should be true if succeed
    peers_org1 = [peer for peer in cli.peers if 'org1' in peer] # assumes peers in org1 are wanted ones

    response = await cli.channel_join(
        requestor=org1_admin,
        channel_name=channel_name,
        peers=peers_org1,
        orderer=orderer)
    if response:
        print("Join channel successful")
    else:
        print("Join channel failed")
        exit(-1)

    # Join peers from a different MSP into Channel
    org2_admin = cli.get_user(org_name='org2.example.com', name=user_name)
    peers_org2 = [peer for peer in cli.peers if 'org2' in peer] # assumes peers in org2 are wanted ones

    response = await cli.channel_join(
        requestor=org2_admin,
        channel_name=channel_name,
        peers=peers_org2,
        orderer=orderer)
    if response:
        print("Join channel successful")
    else:
        print("Join channel failed")
        exit(-1)

    return cli

def set_gopath():
    gopath_bak = os.environ.get('GOPATH', '')
    gopath = os.path.normpath(os.path.join(
        os.path.dirname(os.path.realpath('__file__')),
        CHAINCODE_PATH
    ))
    os.environ['GOPATH'] = os.path.abspath(gopath)
    print("GOPATH:", os.environ['GOPATH'])


async def data_sender_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name):
    """Deploy the data sender chaincode to specified channel.
    :param cli: the client instance for interaction
    """
    set_gopath()
    org1_admin = cli.get_user(org_name=org_name, name=user_name)

    peers_org1 = [peer for peer in cli.peers if 'org1' in peer] # assumes peers in org1 are wanted ones

    # The response should be true if succeed
    response = await cli.chaincode_install(
        requestor=org1_admin,
        peers=peers_org1,
        cc_path='data_sender',
        cc_name=cc_name,
        cc_version=cc_version)
    if response:
        print("Chaincode installed successfully")
        print("Install response:", response)
    else:
        print("Chaincode installation failed")
        exit(-1)

    # Instantiate Chaincode in Channel, the response should be true if succeed
    args = []
    response = await cli.chaincode_instantiate(
        requestor=org1_admin,
        channel_name=channel_name,
        peers=[peer_name],
        args=args,
        cc_name=cc_name,
        cc_version=cc_version,
        wait_for_event=True)
    if response:
        print("Instantiate chaincode completed")
        print("Instantiate response:", response)
    else:
        print("Instantiate chaincode failed with no response")
        exit(-1)

    print("***************************************")
    print("Have the data sender deployed")
    print("***************************************")


async def data_receiver_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name):
    """
    Deploy the data receiver chaincode into the specifed channel.

    :params cli: the client for interaction
    """
    set_gopath()
    org1_admin = cli.get_user(org_name=org_name, name=user_name)

    peers_org1 = [peer for peer in cli.peers if 'org1' in peer] # assumes peers in org1 are wanted ones

    # For data receiver & responder
    # The response should be true if succeed
    response = await cli.chaincode_install(
        requestor=org1_admin,
        peers=peers_org1,
        cc_path='data_receiver',
        cc_name=cc_name,
        cc_version=cc_version)
    if response:
        print("Chaincode installed successfully")
        print("Install response:", response)
    else:
        print("Chaincode installation failed")
        exit(-1)

    # Instantiate Chaincode in Channel, the response should be true if succeed
    args = []
    response = await cli.chaincode_instantiate(
        requestor=org1_admin,
        channel_name=channel_name,
        peers=[peer_name],
        args=args,
        cc_name=cc_name,
        cc_version=cc_version,
        wait_for_event=True)
    if response:
        print("Instantiate chaincode completed")
        print("Instantiate response:", response)
    else:
        print("Instantiate chaincode failed with no response")
        exit(-1)

    print("***************************************")
    print("Have the data receiver deployed")
    print("***************************************")


async def fabric_setup():
    assert sys.argv[1] # ensures a configuration file
    config_file = sys.argv[1]

    parser = ConfigParser()
    try:
        parser.read(config_file)
    except:
        print("Parsing configuration fails...")
        exit(-1)

    # parse the configs for network at left side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'left')
    net_profile = os.path.join('.', net_profile)

    # set up channel and get client
    cli = await channel_setup(net_profile, channel_name, org_name, user_name)

    # deploy chaincodes for data sender 
    await data_sender_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    # parse the configs for network at right side
    (net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name) = parse_fabric(parser, 'right')
    net_profile = os.path.join('.', net_profile)
    
    # deploy chaincodes for data receiver
    await data_receiver_setup(cli, net_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)

    return cli


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fabric_setup())


if __name__ == '__main__':
    main()