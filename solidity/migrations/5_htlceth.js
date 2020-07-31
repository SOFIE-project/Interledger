const Migrations = artifacts.require("Migrations");
const HTLCEth = artifacts.require('HTLCEth');

const fs = require("fs");
const ini = require("ini");

/**
 * Migration script for deploying HTLCEth contract
 * 
 * If network is left, right, compose_left, or compose_right, update the 'contract' 
 * field of the ../local-config.cfg to contain the address of deployed contract,
 * and update 'contract_abi' field to contain the path to the abi file of this
 * contract.
 */
module.exports = async function(deployer, network, accounts) {
    
    await deployer.deploy(Migrations);
    const htlc = await deployer.deploy(HTLCEth);
    
    if (network == "left" || network == "right" ||
        network == "compose_left" || network == "compose_right") {
        
        // update the configuration file
        config_file = "../local-config.cfg";
        base_path = "solidity/contracts/";
     
        const config = ini.parse(fs.readFileSync(config_file, 'utf-8'));
        let net_config = config[network];
        net_config.minter = accounts[0];
        net_config.contract = htlc.address;
        net_config.contract_abi = base_path + "HTLCEth.abi.json";
    
        fs.writeFileSync(config_file, ini.stringify(config));
    }
}
