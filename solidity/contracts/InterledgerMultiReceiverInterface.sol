pragma solidity ^0.5.0;

/**
 * This is the abstract interface to be implemented by every potential data receiver in multi-ledger mode
 */
contract InterledgerMultiReceiverInterface {
    // Event for signalling that recipient agree to accept the incoming data
    event InterledgerInquiryAccepted(uint256 nonce);

    // Event for signalling that recipient agree to accept the incoming data
    event InterledgerInquiryRejected(uint256 nonce);

    /** 
     * @dev Function to inquire whether the recipient will accept the incoming data
     * @param nonce The unique identifier of data event
     * @param data The actual data content encoded in bytes
     */
    function interlegerInquire(uint256 nonce, bytes memory data) public;

    /** 
     * @dev Function to abort the receiving of data involving a particular transaction
     * @param nonce The unique identifier of data event
     * @param reason The error code indicating the reason for failure
     */
    function interledgerReceiveAbort(uint256 nonce, uint256 reason) public;
}