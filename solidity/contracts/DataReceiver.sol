pragma solidity ^0.5.0;

import "./InterledgerReceiverInterface.sol";

/**
 * This is a sample contract as data collector used for develpment and testing
 */
contract DataReceiver is InterledgerReceiverInterface {
    struct DataItem {
        uint256 nonce;
        bytes data;
    }
    
    // sample storage of data for application logic
    DataItem[] public dataItems;

    function interledgerReceive(uint256 nonce, bytes memory payload) public {
        dataItems.push(DataItem(nonce, payload));
        emit InterledgerEventAccepted(nonce);
    }
}
