import pytest
from configparser import ConfigParser


@pytest.fixture
def config():
    config_file = "local-hf-state-manager.cfg"
    parser = ConfigParser()
    parser.read(config_file)

    state_type = parser.get('manager', 'type')
    assert state_type == 'fabric'

    network_profile = parser.get('manager', 'network_profile')
    channel_name = parser.get('manager', 'channel_name')
    cc_name = parser.get('manager', 'cc_name')
    cc_version = parser.get('manager', 'cc_version')
    org_name = parser.get('manager', 'org_name')
    user_name = parser.get('manager', 'user_name')
    peer_name = parser.get('manager', 'peer_name')

    return (network_profile, channel_name, cc_name, cc_version, org_name, user_name, peer_name)
