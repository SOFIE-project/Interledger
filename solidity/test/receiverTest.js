const Receiver = artifacts.require("DataReceiver");

contract("DataReceiver", accounts => {

    /////////////////
    // Testing data
    /////////////////
    const data = "dummy";
    const nonce = 1;

    describe("Testing the DataReceiver functions", function() {

        it("Should receive data", async() => {

            let receiver = await Receiver.deployed();
            //assert.equal(receiver.dataItems().length, 0, "id should be empty");
    
            await receiver.interledgerReceive(nonce,web3.utils.fromUtf8(data));
	    let first = await receiver.dataItems(0);
	    
            assert.equal(first.nonce, 1, "id should be 1");
	    assert.equal(first.data, web3.utils.fromUtf8(data), "data should be dummy");
            
        });
            
    });

});
