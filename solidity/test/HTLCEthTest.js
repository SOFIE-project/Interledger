const HTLCEth = artifacts.require("HTLCEth");

const truffleAssert = require('truffle-assertions');

/**
 * Tests for HTLCEth:
 *  1. depositFunds/require(refundTime > now)
 *  2. depositFunds/require(msg.value > 0)
 *  3. depositFunds/require(receiver != address(0x0))
 *  4. depositFunds/require(receiver != address(this))
 *  5. depositFunds works
 *  6. depositFunds/require(_contracts[lockValue].amount == 0)
 *  7. withdrawFunds/require(lockValue == keccak256(abi.encode(key))
 *  8. withdrawFunds works with correct key
 *  9. withdrawFunds/require(_contracts[lockValue].amount > 0)
 * 10. recoverFunds/require(_contracts[lockValue].amount > 0)
 * 11. depositFunds/require(_contracts[lockValue].withdrawn == false)
 * 12. recoverFunds/require(now > _contracts[lockValue].refundTime)
 * 13. recoverFunds/require(msg.sender == _contracts[lockValue].sender) // maybe not needed?
 * 14. recoverFunds works after timeout
 * 15. can reuse lockValue if no withdrawal has been made
 */
contract("HTLCEth", accounts => {

    const alice = accounts[0]; // sender
    const bob = accounts[1]; // receiver
    const carl = accounts[2]; 
    
    const lockValue1 = "0x5569044719a1ec3b04d0afa9e7a5310c7c0473331d13dc9fafe143b2c4e8148a";
    const key1 = "0x000000000000000000000000000000000000000000000000000000000000007b";
    
    const lockValue2 = "0x9222cbf5d0ddc505a6f2f04716e22c226cee16a955fef88c618922096dae2fd0";
    const key2 = "0x000000000000000000000000000000000000000000000000000000000000007c";
    
    const wrong_key = "0x000000000000000000000000000000000000000000000000000000000000007f";
    const zero_address = "0x0000000000000000000000000000000000000000"

    
    it(" 1. Alice should not be able to deposit funds with refundTime set to past", async() => {
        let htlc = await HTLCEth.deployed();
        
        const refundTime = Math.floor(Date.now() / 1000) - 1;
        
        await truffleAssert.reverts(htlc.depositFunds(bob, lockValue1, refundTime,
                                                      {from: alice, value: 1000}), 
                                    "refundTime should be in the future");
    });

    
    it(" 2. depositFunds() should not work without sending value", async() => {
        let htlc = await HTLCEth.deployed();
        
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        
        await truffleAssert.reverts(htlc.depositFunds(bob, lockValue1, refundTime,
                                                      {from: alice, value: 0}),
                                    "funds must be deposited");
    });

    
    it(" 3. Alice should not be able to deposit funds to '0x0'", async() => {
        let htlc = await HTLCEth.deployed();
        
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await truffleAssert.reverts(htlc.depositFunds(zero_address, lockValue1, refundTime,
                                                      {from: alice, value: 1000}),
                                    "receiver's address can't be 0x0");
    });
    
    
    it(" 4. Alice should not be able to deposit funds to contract address", async() => {
        let htlc = await HTLCEth.deployed();
        
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await truffleAssert.reverts(htlc.depositFunds(htlc.address, lockValue1, refundTime,
                                                      {from: alice, value: 1000}),
                                    "receiver's address can't be this contract");
    });

        
    it(" 5. Alice deposits funds to Bob", async() => {
        let htlc = await HTLCEth.deployed();
    
        // deposit 1000 by alice to bob, with 2 second timeout
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await htlc.depositFunds(bob, lockValue1, refundTime, 
                                    {from: alice, value: 1000});
    });

    
    it(" 6. Should not be possible to alter internal fields using existing lockValue", async() => {
        let htlc = await HTLCEth.deployed();
    
        // deposit 1000 by carl to carl, with 2 second timeout
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await truffleAssert.reverts(htlc.depositFunds(carl, lockValue1, refundTime, 
                                                      {from: carl, value: 1000}),
                                    "lockValue is already in use");
        
    });
    
        
    it(" 7. Should not be possible to withdraw funds with a wrong key", async() => {
        let htlc = await HTLCEth.deployed();
            
        await truffleAssert.reverts(htlc.withdrawFunds(lockValue1, wrong_key), "invalid key");
    });
        
        
    it(" 8. Should be possible to withdraw funds with a correct key", async() => {
        let htlc = await HTLCEth.deployed();
            
        // check that bob's balance has increased by 1000
        const oldBalance = parseInt(await web3.eth.getBalance(bob));
        await htlc.withdrawFunds(lockValue1, key1);
        const newBalance = parseInt(await web3.eth.getBalance(bob));

        assert.equal(newBalance, oldBalance + 1000, 
            "Bob's balance should have increased by 1000wei after withdrawal");
        
        // TODO: check that correct interledger-related events are emitted
        // InterledgerStartSending and InterledgerEventAccepted
        // also check that interledgerReceive works properly
    });
        
        
    it(" 9. Should not be able to withdraw funds twice", async() => {
        let htlc = await HTLCEth.deployed();
            
        await truffleAssert.reverts(htlc.withdrawFunds(lockValue1, key1), "no funds in contract");
    });
        
        
    it("10. Alice should not be able to recover funds after withdrawal", async() =>  {
        let htlc = await HTLCEth.deployed();
            
        await truffleAssert.reverts(htlc.recoverFunds(lockValue1, {from: alice}), "no funds to recover");
    });

    
    it("11. Should not be possible to reuse lockValue after withdrawal has been made", async() => {
        let htlc = await HTLCEth.deployed();
    
        // deposit 1000 by alice to bob, with 2 second timeout
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await truffleAssert.reverts(htlc.depositFunds(bob, lockValue1, refundTime, 
                                                      {from: alice, value: 1000}),
                                    "withdrawal has already been made with this lockValue");
        
    });

    
    it("12. Alice should not be able to recover funds before timeout has been reached", async() => {
        let htlc = await HTLCEth.deployed();
            
        // deposit 1000 by alice to bob, with 1 second timeout
        const refundTime = Math.floor(Date.now() / 1000) + 1;
        await htlc.depositFunds(bob, lockValue2, refundTime, {from: alice, value: 1000});
            
        await truffleAssert.reverts(htlc.recoverFunds(lockValue2, {from: alice}), 
                                    "refundTime hasn't been reached yet");
    });
    
    
    // last three tests might be problematic due to timeouts...
    it("13. Bob should not be able to recover funds", async() => {
        let htlc = await HTLCEth.deployed();
        
        // sleep for a while
        await new Promise(t => setTimeout(t, 3000));
        
        await truffleAssert.reverts(htlc.recoverFunds(lockValue2, {from: bob}),
                                    "only sender can recover funds");
    });


    it("14. Alice should be able to recover funds after timeout", async() => {
        let htlc = await HTLCEth.deployed();
            
        // check that alice's balance has increased by 1000, 
        // need to take used gas into account, and use BN to avoid rounding errors
        var BN = web3.utils.BN;
        const oldBalance = new BN(await web3.eth.getBalance(alice));
            
        const receipt = await htlc.recoverFunds(lockValue2, {from: alice})
        const tx = await web3.eth.getTransaction(receipt.tx);
        const gasUsed = new BN(receipt.receipt.gasUsed);
        const gasPrice = new BN(tx.gasPrice);
        balance = oldBalance.sub(gasPrice.mul(gasUsed)); // oldBalance - (gasPrice * gasUsed)
        balance.add(new BN(1000)); // += 1000
            
        const newBalance = parseInt(await web3.eth.getBalance(alice));
            
        assert.equal(newBalance, balance, 
            "Alice's balance should have increased by 1000wei after recovering funds");
    });

    
    it("15. Should be possible to reuse lockValue if withdrawal has not been made", async() => {
        let htlc = await HTLCEth.deployed();
            
        // deposit 1000 by alice to bob, with 2 second timeout
        const refundTime = Math.floor(Date.now() / 1000) + 2;
        await htlc.depositFunds(bob, lockValue2, refundTime, {from: alice, value: 1000});            
    });
});
