var HDWalletProvider = require("truffle-hdwallet-provider");
const MNEMONIC = 'YOUR WALLET KEY';

module.exports = {
  // You can also follow this format for other networks;
  // see <http://truffleframework.com/docs/advanced/configuration>
  // for more details on how to specify configuration options!
  //

  mocha: {
    reporter: "mocha-multi-reporters",
    reporterOptions: {
      "reporterEnabled": "spec, mocha-junit-reporter",
      "mochaJunitReporterReporterOptions": {
	mochaFile: "../tests/smart_contracts_test_results.xml"
      }
    }
  },
  networks: {
    left: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "*"
    },
    right: {
      host: "127.0.0.1",
      port: 7546,
      network_id: "*"
    },
    rinkeby: {
      provider: function() {
        return new HDWalletProvider(MNEMONIC, "https://rinkeby.infura.io/YOUR_API_KEY")
      },
      network_id: 3,
      gas: 4000000      //make sure this gas allocation isn't over 4M, which is the max
    },
    // for Docker Compose setup
    compose_left: {
        host: "ganache_left",
        port: 7545,
        network_id: "*"
    },
    compose_right: {
        host: "ganache_right",
        port: 7545,
        network_id: "*"
    },
  },
  compilers: {
    solc: {
      version: "0.5.17" // ex:  "0.4.20". (Default: Truffle's installed solc)
    }
  }
};
