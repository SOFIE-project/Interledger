const DataSender = artifacts.require('DataSender');

module.exports = function(deployer) {
  deployer.deploy(DataSender);
}
