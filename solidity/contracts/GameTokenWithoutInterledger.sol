pragma solidity ^0.5.0;

import "./AssetTransferInterface.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721Metadata.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721Burnable.sol";
import "@openzeppelin/contracts/access/roles/MinterRole.sol";

/**
 * ERC721 standard for a decentralized asset exchanging game
 *
 * A ERC721 token implementation including the lifecycle methods: mint and burn.
 * Each token has its ERC721 Id, plus two more data: -uri and -name.
 * The - 'tokenId' corresponds to the Interledger protocol id;
 *      In other words, the ERC implementation uses the token ids as ids for the IL asset transfer protocol.
 * The - 'uri' storage is managed by the ERC721Metadata parent;
 * The - 'name' is managed by this contract.
 *
 * Example:
 *  tokenId = 123
 *  uri = /objects/toys/
 *  name = ball123
 *
 *  Moreover, implementing AssetTransferInterface, each token has a state: Here, TransferOut, NotHere
 *     - 'NotHere' represents the asset identified by the token in use in the game
 *     - 'Here' represents the asset identified by the token tradeable in the Eth blockchain as a ERC721 token
 *     - 'TransferOut' represents the willingness of the asset owner to use the asset back in the game
 */
contract GameTokenWithoutInterledger is ERC721, ERC721Metadata, MinterRole, ERC721Burnable, AssetTransferInterface {

    ////
    // Data
    ////
    struct GameAsset {
        bytes32 name;
        State state;
    }

    event NewTokenAsset(address to, string uri, bytes32 name, uint256 tokenId);

    // Data concerning the asset
    mapping(uint256 => GameAsset) private assetMap;


    ////
    // Modifiers
    ////
    modifier _existingAsset(uint256 tokenId) {
        require(assetMap[tokenId].name != 0x0, "GameToken: The asset must be created");
        _;
    }


    ////
    // Functions
    ////
    constructor (string memory title, string memory symbol) public ERC721Metadata(title, symbol) { }


    ////
    // Lifecycle
    ////    

    /// @notice Mint a new token
    /// @dev Call the ERC721 mint and ERC721Metadata setTokenURI (internal) functions
    /// @param to The receiver of the token
    /// @param tokenId The token id
    /// @param tokenURI The URI describing the token
    /// @param name The paired name of the token
    function mint(address to, uint256 tokenId, string memory tokenURI, bytes32 name) public onlyMinter returns (bool) {

        super._mint(to, tokenId);
        super._setTokenURI(tokenId, tokenURI);

        // When a token is minted is not currently in trading mode
        assetMap[tokenId] = GameAsset(name, State.NotHere);

        emit NewTokenAsset(to, tokenURI, name, tokenId);

        return true;
    }


    /// @notice Burn an existing token
    /// @dev Override the ERC721Burnable burn (public) function. The correctness is checked on the parent function
    /// @param tokenId The token id
    function burn(uint256 tokenId) public {
        super.burn(tokenId);

        delete assetMap[tokenId];
    }


    ////
    // Token State Management
    ////    

    // enum State { NotHere,       // 0
    //              TransferOut,   // 1
    //              Here}          // 2

    // Transitions:
        // 2 -> 1: owner,   transferOut operation
        // 1 -> 2: creator, abort       operation
        // 1 -> 0: creator, accept      operation
        // 0 -> 2: creator, commit      operation
    

    /// @notice Set the token to TransferOut state
    /// @dev The asset changes state Here -> TransferOut. Callable by the asset owner
    /// @param tokenId The token id 
    function transferOut(uint256 tokenId) public _existingAsset(tokenId) {

        require(ownerOf(tokenId) == msg.sender, "GameToken: Only then owner of this token can perform this operation");
        require(assetMap[tokenId].state == State.Here, "GameToken: tokenId must be in Here state");

        assetMap[tokenId].state = State.TransferOut;
        //bytes memory data = abi.encode(tokenId);
        //emit InterledgerEventSending(tokenId, data);
    }

    /// @notice Set the token to NotHere state
    /// @dev The asset changes state TransferOut -> NotHere. Callable by the game authority
    /// @param tokenId The token id 
    function interledgerCommit(uint256 tokenId) public onlyMinter _existingAsset(tokenId) {
        
        require(assetMap[tokenId].state == State.TransferOut, "GameToken: tokenId must be in TransferOut state");

        assetMap[tokenId].state = State.NotHere;
        emit NotHere(msg.sender, assetMap[tokenId].name, tokenId);
    }

    // For KSI
    function interledgerCommit(uint256 tokenId, bytes memory data) public onlyMinter _existingAsset(tokenId){
        //TODO check the hash value (i.e. data)
        require(assetMap[tokenId].state == State.TransferOut, "GameToken: tokenId must be in TransferOut state");

        assetMap[tokenId].state = State.NotHere;
        emit NotHere(msg.sender, assetMap[tokenId].name, tokenId);
    }

    /// @notice Set the token to Here state, to use to handle errors
    /// @dev The asset changes state TransferOut -> Here. Callable by the game authority
    /// @param tokenId The token id 
    /// @param reason The reason 
    function interledgerAbort(uint256 tokenId, uint256 reason) public onlyMinter _existingAsset(tokenId) {
        
        require(assetMap[tokenId].state == State.TransferOut, "GameToken: tokenId must be in TransferOut state");

        assetMap[tokenId].state = State.Here;
        emit Here(msg.sender, assetMap[tokenId].name, tokenId);
    }

    /// @notice Set the token to Here state
    /// @dev The asset changes state NotHere -> Here. Callable by the game authority
    /// @param tokenId The token id 
    function accept(uint256 tokenId) public onlyMinter _existingAsset(tokenId) {

        require(assetMap[tokenId].state == State.NotHere, "GameToken: tokenId must be in NotHere state");

        assetMap[tokenId].state = State.Here;
        emit Here(msg.sender, assetMap[tokenId].name, tokenId);
    }


    ////
    // ERC721 Modifications
    ////

    /// @notice Transfer a token only if it is in Trading Mode
    /// @param from current owner of the token
    /// @param to address to receive the ownership of the given token ID
    /// @param tokenId uint256 ID of the token to be transferred
    function _transferFrom(address from, address to, uint256 tokenId) internal _existingAsset(tokenId) {

        require(assetMap[tokenId].state == State.Here, "GameToken: tokenId must be in Here state");

        super._transferFrom(from, to, tokenId);
    }

    ////
    // GETTERS
    ////

    /// @notice Get the name paired to the token
    /// @param tokenId The token id
    /// @return { The paired name }
    function getAssetNameOfToken(uint256 tokenId) public view returns(bytes32) {

        return assetMap[tokenId].name;
    }


    /// @notice Get the current state of the token
    /// @param tokenId The token id
    /// @return { The token state }
    function getStateOfToken(uint256 tokenId) public view returns(State) {

        return assetMap[tokenId].state;
    }

}

