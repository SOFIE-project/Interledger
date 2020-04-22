pragma solidity ^0.5.0;

/**
* Abstract contract exposing the methods, data structure and events to manage state transition for Interledger protocol in Ethereum.
*/
contract AssetTransferInterface {
    // States
    enum State { NotHere,       // 0
                 TransferOut,   // 1
                 Here}          // 2

    // Transitions:
        // 2 -> 1: owner,   transferOut operation
        // 1 -> 2: creator, abort       operation
        // 1 -> 0: creator, accept      operation
        // 0 -> 2: creator, commit      operation
    
    event Here(address from, bytes32 data, uint256 id);
    event TransferOut(address from, bytes32 data, uint256 id);
    event NotHere(address from, bytes32 data, uint256 id);

    /// @notice Set the token to TransferOut state
    /// @param id id value 
    function transferOut(uint256 id) public;


    /// @notice Set the token to Here state
    /// @param id id value 
    function accept(uint256 id) public;
}
