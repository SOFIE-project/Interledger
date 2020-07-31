const Migrations = artifacts.require("Migrations");
const DataTransceiver = artifacts.require("DataTransceiver");

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
module.exports = function(deployer, network) {

  deployer.then(async () => {
    
    // Since ganache needs to be restarted every time, the deployed contract address will 
	  // be different, therefore store the address of the contract to the configuration file
    if(network == "left" || network == "right" || 
		network == "compose_left" || network == "compose_right") {

      await deployer.deploy(Migrations);
      const data_transceiver = await deployer.deploy(DataTransceiver);

      const config = ini.parse(fs.readFileSync('../local-config.cfg', 'utf-8'));

      base_path = "solidity/contracts/";
      net_config = config[network]
      net_config.contract = data_transceiver.address
      net_config.contract_abi = base_path + "DataTransceiver.abi.json";

      const iniText = ini.stringify(config);
      fs.writeFileSync('../local-config.cfg', iniText);
    } else {

      // Loca truffle test network if development is not present in config
      await deployer.deploy(Migrations);
      data_transceiver = await deployer.deploy(DataTransceiver);

    }
  });
};
