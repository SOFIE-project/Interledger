pragma solidity ^0.5.0;

/**
 * This is the abstract interface to be implemented by potential data sender
 */
contract InterledgerSenderInterface {
    // Event for sending data to another ledger
    event InterledgerEventSending(uint256 id, bytes data);

    /**
     * @dev Function that will be called when the recipient has accepted the data 
     * @param id The identifier of data sending event
     */
    function interledgerCommit(uint256 id) public;


    /**
     * @dev Function that will be called when the recipient has accepted the data,
	 *		this function contains also an additional data parameter, which can be
	 *		used to pass information to the Sender. Used by e.g. KSI Responder 
	 * 		to pass KSI id back to the Sender.
     * @param id The identifier of data sending event
     * @param data Arbitrary data as bytes
     */
    function interledgerCommit(uint256 id, bytes memory data) public;


    /**
     * @dev Function that will be called when the recipient has rejected the data, 
     *      or there have been an error.
     * @param id The identifier of data sending event
     * @param reason The error code indicating the reason for failure
     */
    function interledgerAbort(uint256 id, uint256 reason) public;
}
