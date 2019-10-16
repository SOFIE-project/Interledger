const Migrations = artifacts.require("Migrations");
const GameToken = artifacts.require("GameToken");

const fs = require("fs");
const ini = require("ini");

/**
 * Migration script
 * 
 * Network development:
 *  - deploy the token contract
 * 
 * Networks ganache8545 and ganache7545
 *  - deploy the token contract
 *  - update the configuration file ../local-config.cfg
 * 
 * Otherwise:
 *  - deploy the token contract
 */
module.exports = function(deployer, network, accounts) {

  deployer.then(async () => {

    alice = accounts[0];

    if(network == "development") {

      await deployer.deploy(Migrations);
      token = await deployer.deploy(GameToken, "GameToken", "GAME", {'from': alice});
    }
    
    // Example for local configuration
      // Since ganache needs to be restarted every time, the deployed contract address will be different
      // Store in the local-config file the address of the contract and its minter
      // For testing or demo
    if(network == "ganache8545" || network == "ganache7545") {

      await deployer.deploy(Migrations);
      token = await deployer.deploy(GameToken, "GameToken", "GAME", {'from': alice});

      const config = ini.parse(fs.readFileSync('../local-config.cfg', 'utf-8'));
      net_config = config[network]
      net_config.minter = alice
      net_config.contract = token.address

      const iniText = ini.stringify(config);
      fs.writeFileSync('../local-config.cfg', iniText);
    }
    else {

      // Loca truffle test network if development is not present in config
      await deployer.deploy(Migrations);
      token = await deployer.deploy(GameToken, "GameToken", "GAME", {'from': alice});

    }
  });
};
