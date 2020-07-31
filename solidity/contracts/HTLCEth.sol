pragma solidity ^0.5.0;

import "./InterledgerReceiverInterface.sol";
import "./InterledgerSenderInterface.sol";

contract HTLCEth is InterledgerSenderInterface, InterledgerReceiverInterface {
    
    /**
     * Example implementation of Hash Time Locked Contract (HTLC) for Interledger.
     * HTLC allows parties (A and B in this example) to exchange assets securely. 
     * This HTLC implementation allows parties to exchange ethers, and it can be exteneded
     * to support the exchange of any kind of ledger-based assets. The implementation works 
     * as follows (both A and B act as a sender in their smart contracts, and as a receiver 
     * in other party's smart contract):
     * 
     * 1. Sender deposits funds using depositFunds() by specifying a receiver, 
     *    lock value H(s) and time when funds be available for refund (timeout).
     * 
     * 2. Anyone can unlock the fund transfer to the receiver by calling withdrawFunds()
     *    with a proper lock value and key.
     * 
     * 3. If the funds have not been withdrawn, the sender can receive its funds back after 
     *    the timeout by providing a lock value to the recoverFunds().
     * 
     * 
     * SOFIE Interledger component can be used to automate the last step of the exchange in a 
     * case where the assets and associated smart contracts are located on different ledgers: 
     * 1. The Interledger component is listening for events emitted by B's smart contract.
     * 
     * 2. On B's smart contract, withdrawFunds() function (if withdrawal is successful) 
     *    emits InterledgerEventSending event containing lock value and secret key 
     *    packed as data field of the event.
     * 
     * 3. After receiving an event from B's ledger, Interledger calls interledgerReceive()
     *    function from A's ledger, with the received data from B's ledger as the payload.
     * 
     * 4. interledgerReceive() on A's ledger unpacks the values (lock value and secret key) 
     *    and calls withdrawFunds() function with these values, which will result 
     *    in transfering assets to B.
     */
    
    /**
     * Stores conract information, lockValue (H(s)) acts as the key to ContractData: 
     * sender       - party that deposits the assets
     * receiver     - party that should receive the assets
     * amount       - amount that has been deposited
     * refundTime   - time after which sender can recover assets
     * withdrawn    - wherever assets corresponding to this lockValue have already
     *                been withdrawn
     */
    struct ContractData {
        address payable sender;
        address payable receiver;
        uint256 amount; 
        uint256 refundTime;
        bool withdrawn;
    }
    
    // mapping between lockValue and ContractData
    mapping(bytes32 => ContractData) private _contracts;

    // for debugging
    event debug(bytes32 lockValue, address payable sender,
        address payable receiver, uint256 amount, uint256 timeAvailable);
        
    constructor () public { }
    

    /**
     * @notice Deposits funds for a certain receiver to the contract, locked by lock value
     * @dev While anyone can later initiate withdrawal, only the sender can recover funds 
     * @param receiver Receiver's address
     * @param lockValue Keccak256 hash of the secrect key
     * @param refundTime Timestamp, after which funds can be recovered using recovedFunds()
     */
    function depositFunds(address payable receiver, bytes32 lockValue, uint256 refundTime) public payable {
        // check that lockvalue isn't in use (and the secret hasn't been revealed previously through withdrawal),
        // msg.value is > 0, refundTime is in the future, and receiver's address is sensible
        require(_contracts[lockValue].amount == 0, "lockValue is already in use");
        require(_contracts[lockValue].withdrawn == false, "withdrawal has already been made with this lockValue");
        require(refundTime > now, "refundTime should be in the future");
        require(msg.value > 0, "funds must be deposited");
        require(receiver != address(0x0), "receiver's address can't be 0x0");
        require(receiver != address(this), "receiver's address can't be this contract");

        
        _contracts[lockValue] = ContractData(msg.sender, receiver, msg.value, refundTime, false);
        
        emit debug(lockValue, _contracts[lockValue].sender, _contracts[lockValue].receiver, 
            _contracts[lockValue].amount, _contracts[lockValue].refundTime);
            
    }
    
    
    /**
     * @notice Transfers assets to the receiver, requires a correct key that matches lockValue
     * @dev Anyone can initiate withdrawal by providing a correct key
     * @param lockValue Keccak256 hash of the secrect key
     * @param key The corresponding secret key
     */
    function withdrawFunds(bytes32 lockValue, bytes32 key) public {
        // check that contract has funds and key is correct
        require(_contracts[lockValue].amount > 0, "no funds in contract");
        require(lockValue == keccak256(abi.encode(key)), "invalid key");
        
        uint256 value = _contracts[lockValue].amount;
        _contracts[lockValue].amount = 0;
        _contracts[lockValue].withdrawn = true;
        
        _contracts[lockValue].receiver.transfer(value);
        
        // emit an event to start the Interledger process, 
        // necessary information (lockValue + key) is provided as data parameter
        bytes memory data = abi.encode(lockValue, key);
        emit InterledgerEventSending(uint256(_contracts[lockValue].sender), data);
    }
    
    
    /**
     * @notice Callable by sender to recover funds after the timeout period has passed
     * @param lockValue Lock value is used to identify the original deposit
     */
    function recoverFunds(bytes32 lockValue) public {
        // check that caller is valid, contract has funds, and enough time has passed
        require(msg.sender == _contracts[lockValue].sender, "only sender can recover funds");
        require(_contracts[lockValue].amount > 0, "no funds to recover");
        require(now > _contracts[lockValue].refundTime, "refundTime hasn't been reached yet");
        
        uint256 value = _contracts[lockValue].amount;
        _contracts[lockValue].amount = 0;
        _contracts[lockValue].sender.transfer(value);
    }
    
    
    // Interledger-related functions
    
    /**
     * @notice Called by Interledger, unpacks necessary values and calls withdrawFunds()
     * @param nonce Nonce sent by the Interledger component
     * @param data Data sent by the Interledger component, contains lockValue and key
     */
    function interledgerReceive(uint256 nonce, bytes memory data) public {

        // unpack parameters from data and call withdrawFunds()
        (bytes32 lockValue, bytes32 key) = abi.decode(data, (bytes32, bytes32));

        withdrawFunds(lockValue, key);
        
        emit InterledgerEventAccepted(nonce);
    }
    
    
    // For processing results of interledgerReceive on the other ledger
    function interledgerCommit(uint256 identity) public { }

    function interledgerCommit(uint256 id, bytes memory data) public { }
    
    function interledgerAbort(uint256 id, uint256 reason) public { }
}
