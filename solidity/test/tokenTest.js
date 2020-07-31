const Token = artifacts.require("GameToken");

contract("GameToken", accounts => {

    const alice = accounts[0]; // First seller
    const bob = accounts[2];   // Second seller
    const carl = accounts[3];   // Buyer

    const price = web3.utils.toWei('1', 'ether');

    const BN = web3.utils.BN;

    /////////////////
    // Testing data
    /////////////////
    const tokenId = 123;
    const tokenId2 = 321;
    const abortReason = 42;

    const object1 = {id: "VorpalSword1",
                     uri: "game/weapons/"};
    const object2 = {id: "Hammer1",
                     uri: "game/toys/"};
    const object3 = {id: "Hammer2",
                     uri: "game/toys/"};

    const objects = [object1, object2, object3];

    const NOT_HERE = 0;
    const TRANSFER_OUT = 1;
    const HERE = 2;

    describe("Testing the lifecycle functions", function() {

        it("Should mint a new token", async() => {

            let token = await Token.deployed();
            assert.equal(await token.isMinter(alice), true, "Minter should be " + alice);
    
            await token.mint(bob, tokenId, object1.uri, web3.utils.fromUtf8(object1.id));
            assert.equal(await token.balanceOf(bob), 1, "Bob should have 1 token");
            assert.equal(web3.utils.toUtf8(await token.getAssetNameOfToken(tokenId)), object1.id, "Token " + tokenId + " should be paired to assetId " + object1.id);
            assert.equal(await token.getStateOfToken(tokenId), NOT_HERE, "token should have state "+NOT_HERE+": NotHere");
        });
            
        it("Should burn a minted token", async() => {
    
            let token = await Token.deployed();
    
            await token.burn(tokenId, {from: bob});
            assert.equal(await token.balanceOf(bob), 0, "Bob should have 0 tokens");
            assert.equal(await token.getAssetNameOfToken(tokenId), 0x0, "Token " + tokenId + " should be paired to assetId " + object1.id);
        });
    });

    describe("Testing the state change and transfer of a token", function() {

        it("Should mint a token and put it in trading mode On", async() => {

            let token = await Token.deployed();
    
            await token.mint(bob, tokenId, object1.uri, web3.utils.fromUtf8(object1.id));
            
            // The game puts the token Here
            await token.accept(tokenId, {from: alice});
            assert.equal(await token.getStateOfToken(tokenId), HERE, "token should have state "+HERE+": Here");
        });
    
        it("Bob should tranfer its token to Carl", async() => {
    
            let token = await Token.deployed();
    
            // Transfer the token
            await token.transferFrom(bob, carl, tokenId, {from: bob});
            assert.equal(await token.ownerOf(tokenId), carl, "Carl should have received a token from Bob");
            assert.equal(await token.getStateOfToken(tokenId), HERE, "token " + tokenId + " should have state "+HERE+": Here");
       });
    
       it("Carl wishes to use the token " + tokenId + " in the game", async() => {
    
            let token = await Token.deployed();
    
            // Carl
            await token.transferOut(tokenId, {from: carl});
            assert.equal(await token.getStateOfToken(tokenId), TRANSFER_OUT, "token " + tokenId + " should have state "+TRANSFER_OUT+": TransferOut");
        });

        it("Should NOT be possible to trade the token " + tokenId + " because it is not in Here state", async() => {

            let token = await Token.deployed();
        
            await token.transferFrom(carl, bob, tokenId, {from: carl}).then(assert.fail).catch(function(error) {
                // Should fail because there is no commitment AND the token is NotHere state
                assert(error.message.indexOf('revert') >= 0, "Carl cannot transfer token " + tokenId + ", because the token in WantToUse state");            
            });
        });

        it("Should finalize state change of the token " + tokenId, async() => {
    
            let token = await Token.deployed();
    
            // Game authority
            await token.interledgerCommit(tokenId, {from: alice});
            assert.equal(await token.getStateOfToken(tokenId), NOT_HERE, "token should have state "+NOT_HERE+": NotHere");
        });

        it("Should NOT be possible to trade the token " + tokenId + " because it is not in Here state", async() => {

            let token = await Token.deployed();
        
            await token.transferFrom(carl, bob, tokenId, {from: carl}).then(assert.fail).catch(function(error) {
                // Should fail because there is no commitment AND the token is NotHere state
                assert(error.message.indexOf('revert') >= 0, "Carl cannot transfer token " + tokenId + ", because the token in NotHere state");            
            });
        });
        
    });

    describe("Burn the token", function() {

        it("Carl should burn the token " + tokenId, async() => {

            let token = await Token.deployed();
    
            await token.burn(tokenId, {from: carl});
            assert.equal(await token.balanceOf(carl), 0, "Bob should have 0 tokens");
            assert.equal(await token.getAssetNameOfToken(tokenId), 0x0, "Token " + tokenId + " should be empty: 0x0");
        });
    });


    describe("Testing the aborting transfer of a token", function() {

	it("Should mint a token and put it in trading mode On", async() => {

	    let token = await Token.deployed();
	    await token.mint(bob, tokenId, object1.uri, web3.utils.fromUtf8(object1.id));
	    // The game puts the token Here
	    await token.accept(tokenId, {from: alice});
	    assert.equal(await token.getStateOfToken(tokenId), HERE, "token should have state "+HERE+": Here");

	    // Transfer the token
	    await token.transferOut(tokenId, {from: bob});
	    assert.equal(await token.getStateOfToken(tokenId), TRANSFER_OUT, "token " + tokenId + " should have state "+TRANSFER_OUT+": TransferOut");
            //abort transfering the token
	    await token.interledgerAbort(tokenId, abortReason, {from: alice});
	    assert.equal(await token.getStateOfToken(tokenId), HERE, "token should have state "+HERE+": Here");

	});
    });

});
