const Sender = artifacts.require("DataSender");

contract("DataSender", accounts => {

    /////////////////
    // Testing data
    /////////////////
    const data = "data";


    describe("Testing the DataSender functions", function() {

        it("Should send data", async() => {

            let sender = await Sender.deployed();
            assert.equal(await sender.id(), 0, "id should be 0");
    
            await sender.emitData(web3.utils.fromUtf8(data));
            assert.equal(await sender.id(), 1, "id should be 1");
            
        });
            
    });

});
