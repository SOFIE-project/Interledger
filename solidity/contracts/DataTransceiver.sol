pragma solidity ^0.5.0;

import "./InterledgerReceiverInterface.sol";
import "./InterledgerSenderInterface.sol";


/**
 * This is a sample contract as data sender used for develpment and testing
 */
contract DataTransceiver is InterledgerSenderInterface, InterledgerReceiverInterface {

    struct DataItem {
        uint256 nonce;
        bytes data;
    }
    
    // sample storage of data for application logic
    DataItem[] public dataItems;
    uint256 public id;

    /**
     * @dev have an initial identifier
     */
    constructor() public {
        id = 0;
    }
    
    /**
     * @dev application logic to emit data to another ledger via event
     * @param data encoded data content in bytes
     */
    function emitData(bytes memory data) public {
        id += 1;
        emit InterledgerEventSending(id, data);
    }

    function interledgerCommit(uint256 identity) public {

    }

    // For KSI
    function interledgerCommit(uint256 identity, bytes memory data) public {

    }

    function interledgerAbort(uint256 identity, uint256 reason) public {

    }

    function interledgerReceive(uint256 nonce, bytes memory payload) public {
        dataItems.push(DataItem(nonce, payload));
        emit InterledgerEventAccepted(nonce);
    }
}

