pragma solidity ^0.5.0;

import "./InterledgerReceiverInterface.sol";
import "./InterledgerMultiReceiverInterface.sol";

/**
 * This is a sample contract as multi-ledger data collector used for develpment and testing
 */
contract DataMultiReceiver is InterledgerReceiverInterface, InterledgerMultiReceiverInterface {
    struct DataItem {
        uint256 nonce;
        bytes data;
    }
    
    // sample storage of data for application logic
    DataItem[] public dataItems;

    function interlegerInquire(uint256 nonce, bytes memory data) public {
        emit InterledgerInquiryAccepted(nonce);
    }

    function interledgerReceive(uint256 nonce, bytes memory payload) public {
        dataItems.push(DataItem(nonce, payload));
        emit InterledgerEventAccepted(nonce);
    }

    function interledgerReceiveAbort(uint256 nonce, uint256 reason) public {
        emit InterledgerEventRejected(nonce);
    }
}
