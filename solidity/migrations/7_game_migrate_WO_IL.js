const Migrations = artifacts.require("Migrations");
const GameToken = artifacts.require("GameTokenWithoutInterledger");

const fs = require("fs");
const ini = require("ini");

/**
 * Migration script
 * 
 * Network development:
 *  - deploy the token contract
 * 
 * Networks left, right, compose_left, compose_right
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
      const token = await deployer.deploy(GameToken, "GameTokenWithoutInterledger", "GAME", {'from': alice});
    }
    
    // Since ganache needs to be restarted every time, the deployed contract address will 
    // be different. Store in the local-config file the address of the contract and its minter
    // for testing or demo.
    if(network == "left" || network == "right" ||
        network == "compose_left" || network == "compose_right") {

      await deployer.deploy(Migrations);
      token = await deployer.deploy(GameToken, "GameTokenWithoutInterledger", "GAME", {'from': alice});

      base_path = "solidity/contracts/";
      const config = ini.parse(fs.readFileSync('../local-config.cfg', 'utf-8'));
      net_config = config[network]
      net_config.minter = alice
      net_config.contract = token.address
      net_config.contract_abi = base_path + "GameTokenWithoutInterledger.abi.json";

      const iniText = ini.stringify(config);
      fs.writeFileSync('../local-config.cfg', iniText);
    } else {

      // Local truffle test network if development is not present in config
      await deployer.deploy(Migrations);
      token = await deployer.deploy(GameToken, "GameToken", "GAME", {'from': alice});

    }
  });
};
