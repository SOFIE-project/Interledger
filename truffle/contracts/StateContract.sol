pragma solidity ^0.5.0;

/**
* Abstract contract exposing the methods, data structure and events to manage state transition for Interledger protocol in Ethereum.
*/
contract StateContract {
    // States
    enum State { Here,        // 1
                 TransferOut, // 2
                 NotHere}     // 3

    // Transitions:
        // 1 -> 2: owner
        // 2 -> 1: authority
        // 2 -> 3: authority
        // 3 -> 1: authority
    
    event Here(address from, bytes32 data, uint256 id);
    event TransferOut(address from, bytes32 data, uint256 id);
    event NotHere(address from, bytes32 data, uint256 id);

    /// @notice Set the token to TransferOut state
    /// @param id id value 
    function transferOut(uint256 id) public;

    /// @notice Set the token to NotHere state
    /// @param id id value 
    function commit(uint256 id) public;

    /// @notice Set the token to Here state
    /// @param id id value 
    function accept(uint256 id) public;

    /// @notice Set the token to Here state, to use to handle errors
    /// @param tokenId The token id 
    function abort(uint256 tokenId) public;
}