# Hash Storage with KSI

Interledger component supports storing hashes to the [Guardtime KSI](https://guardtime.com/technology) blockchain using the [Catena DB](https://tryout-catena.guardtime.net/swagger/) service. This can be used to e.g. improve privacy and provide auditability and transparency: private data is kept on a private ledger, while a hash of the data is stored on KSI to provide immutability for the data (if the original data is modified in any way, the hash verification would fail). 

When using KSI with Interledger, the KSI Responder of the Interledger component *automatically calculates the hash* over the data emitted in *InterledgerEventSending()* event, and stores this hash value to KSI, which in turn generates a new KSI signature. The resulting signature id will be passed to the sending ledger using the modified *interledgerCommit()* function described below. The signature can then be verified by the user using the [Catena DB](https://tryout-catena.guardtime.net/swagger/#!/KSI32Signatures/getUsingGET_V1) service.


## Smart Contract Interface

In order to support reception of the KSI signature id, the *Initiator* ledger must implement a *interledgerCommit()* function with an additional `data` parameter that will be used to pass the KSI signature id, as shown in the [InterledgerSenderInterface](../solidity/contracts/InterledgerSenderInterface.sol) definition:

    /**
     * @dev Function that will be called when the recipient has accepted the data,
     *      this function contains also an additional data parameter, which can be
     *      used to pass information to the Sender. Used by e.g. KSI Responder 
     *      to pass KSI id back to the Sender.
     * @param id The identifier of data sending event
     * @param data Arbitrary data as bytes
     */
    function interledgerCommit(uint256 id, bytes memory data) public;


## Configuration 

The KSI can only be used as the destination ledger, so the Interledger setup must be unidirectional and `direction` parameter must be set to either `left-to-right` in which case KSI must be the right ledger, or to `right-to-left` in which case KSI must be the left ledger. 

For ledger `type` =  `ksi`, the required options in the configuration file are:

- **url:** the URL for Catena signatures API;
- **hash_algorithm:** the hash algorithm supported by Catena;
- **username:** the username for Catena service;
- **password:** the password for Catena service.

An example of the configuration file using left-to-right bridge between Ethereum and KSI:

    [service]
    direction=left-to-right
    left=ethereum
    right=ksi

    [ethereum]
    type=ethereum
    url=http://localhost
    port=7545
    minter=0x63f7e0a227bCCD4701aB459b837446Ce61aaEb6D
    contract=0x50dc31410Cae2527b034233338B85872BE67EEe6
    contract_abi=./solidity/contracts/DataSender.abi.sol

    [ksi]
    type=ksi
    url=https://tryout-catena-db.guardtime.net/api/v1/signatures
    hash_algorithm=SHA-256
    username=catena_username
    password=catena_password
    
    
