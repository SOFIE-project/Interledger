pragma solidity ^0.5.0;

/**
 * This is the abstract interface to be implemented by potential data receiver
 */
contract InterledgerReceiverInterface {
    // Event for signalling that the recipient has accepted the data
    event InterledgerEventAccepted(uint256 nonce);

    // Event for signalling that the recipient has rejected the data
    event InterledgerEventRejected(uint256 nonce);

    /**
     * @dev Function to receive data from Interledger
     * @param nonce The unique identifier of data event
     * @param data The actual data content encoded in bytes
     */
    function interledgerReceive(uint256 nonce, bytes memory data) public;
}
