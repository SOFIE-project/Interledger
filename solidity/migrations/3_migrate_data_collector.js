const DataReceiver = artifacts.require('DataReceiver');

module.exports = function(deployer) {
  deployer.deploy(DataReceiver);
}
