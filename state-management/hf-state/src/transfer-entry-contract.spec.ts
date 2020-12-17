/*
 * SPDX-License-Identifier: Apache-2.0
 */

import { Context } from 'fabric-contract-api';
import { ChaincodeStub, ClientIdentity } from 'fabric-shim';
import { TransferStatus, TransferEntryContract } from '.';

import * as chai from 'chai';
import * as chaiAsPromised from 'chai-as-promised';
import * as sinon from 'sinon';
import * as sinonChai from 'sinon-chai';
import winston = require('winston');

chai.should();
chai.use(chaiAsPromised);
chai.use(sinonChai);

class TestContext implements Context {
    public stub: sinon.SinonStubbedInstance<ChaincodeStub> = sinon.createStubInstance(ChaincodeStub);
    public clientIdentity: sinon.SinonStubbedInstance<ClientIdentity> = sinon.createStubInstance(ClientIdentity);
    public logging = {
        getLogger: sinon.stub().returns(sinon.createStubInstance(winston.createLogger().constructor)),
        setLevel: sinon.stub(),
     };
}

describe('TransferEntryContract', () => {

    let contract: TransferEntryContract;
    let ctx: TestContext;

    beforeEach(() => {
        contract = new TransferEntryContract();
        ctx = new TestContext();
        ctx.stub.getState.withArgs('1001').resolves(Buffer.from('{"value":"my asset 1001 value"}'));
        ctx.stub.getState.withArgs('1002').resolves(Buffer.from('{"value":"my asset 1002 value"}'));
    });

    describe('#transferEntryExists', () => {

        it('should return true for a my asset', async () => {
            await contract.transferEntryExists(ctx, '1001').should.eventually.be.true;
        });

        it('should return false for a my asset that does not exist', async () => {
            await contract.transferEntryExists(ctx, '1003').should.eventually.be.false;
        });

    });

    describe('#createTransferEntry', () => {

        it('should create a my asset', async () => {
            await contract.createTransferEntry(ctx, '1003', '0xnonce123', '0xdata456');
            ctx.stub.putState.should.have.been.calledOnceWithExactly('1003', Buffer.from('{"value":"my asset 1003 value"}'));
        });

        it('should throw an error for a my asset that already exists', async () => {
            await contract.createTransferEntry(ctx, '1001', '0xnonce123', '0xdata456').should.be.rejectedWith(/The my asset 1001 already exists/);
        });

    });

    describe('#readTransferEntry', () => {

        it('should return a my asset', async () => {
            await contract.readTransferEntry(ctx, '1001').should.eventually.deep.equal({ value: 'my asset 1001 value' });
        });

        it('should throw an error for a my asset that does not exist', async () => {
            await contract.readTransferEntry(ctx, '1003').should.be.rejectedWith(/The my asset 1003 does not exist/);
        });

    });

    describe('#updateTransferEntry', () => {

        it('should update a my asset', async () => {
            await contract.updateTransferEntry(ctx, '1001', TransferStatus.SENT);
            ctx.stub.putState.should.have.been.calledOnceWithExactly('1001', TransferStatus.SENT);
        });

        it('should throw an error for a my asset that does not exist', async () => {
            await contract.updateTransferEntry(ctx, '1003', TransferStatus.SENT).should.be.rejectedWith(/The my asset 1003 does not exist/);
        });

    });

    describe('#deleteTransferEntry', () => {

        it('should delete a my asset', async () => {
            await contract.deleteTransferEntry(ctx, '1001');
            ctx.stub.deleteState.should.have.been.calledOnceWithExactly('1001');
        });

        it('should throw an error for a my asset that does not exist', async () => {
            await contract.deleteTransferEntry(ctx, '1003').should.be.rejectedWith(/The my asset 1003 does not exist/);
        });

    });

});
