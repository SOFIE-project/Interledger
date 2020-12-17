/*
 * SPDX-License-Identifier: Apache-2.0
 */

import { Context, Contract, Info, Returns, Transaction } from 'fabric-contract-api';
import { send } from 'process';
import { TransferStatus, TransferEntry } from './transfer-entry';

@Info({ title: 'TransferEntryContract', description: 'The smart contract for the transfer entries.' })
export class TransferEntryContract extends Contract {

    @Transaction(false)
    @Returns('boolean')
    public async transferEntryExists(ctx: Context, transferEntryId: string): Promise<boolean> {
        const buffer = await ctx.stub.getState(transferEntryId);
        return (!!buffer && buffer.length > 0);
    }

    @Transaction()
    public async createTransferEntry(ctx: Context, transferEntryId: string, nonce: string, data: string): Promise<void> {
        const exists = await this.transferEntryExists(ctx, transferEntryId);
        if (exists) {
            throw new Error(`The transfer entry ${transferEntryId} already exists`);
        }
        const transferEntry = new TransferEntry();
        transferEntry.payload = { id: transferEntryId, nonce, data };
        const buffer = Buffer.from(JSON.stringify(transferEntry));
        await ctx.stub.putState(transferEntryId, buffer);

        ctx.stub.setEvent('transferReady', buffer);
    }

    @Transaction(false)
    @Returns('transferEntry')
    public async readTransferEntry(ctx: Context, transferEntryId: string): Promise<TransferEntry> {
        const exists = await this.transferEntryExists(ctx, transferEntryId);
        if (!exists) {
            throw new Error(`The transfer entry ${transferEntryId} does not exist`);
        }
        const buffer = await ctx.stub.getState(transferEntryId);
        const transferEntry = JSON.parse(buffer.toString()) as TransferEntry;
        return transferEntry;
    }

    @Transaction()
    public async updateTransferEntry(
        ctx: Context,
        transferEntryId: string,
        status?: TransferStatus,
        sendAcceptance?: boolean,
        result?: string): Promise<void> {

        const exists = await this.transferEntryExists(ctx, transferEntryId);
        if (!exists) {
            throw new Error(`The transfer entry ${transferEntryId} does not exist`);
        }

        let buffer = await ctx.stub.getState(transferEntryId);
        const transferEntry = JSON.parse(buffer.toString()) as TransferEntry;

        // update the transfer entry object
        transferEntry.status = status;

        if (sendAcceptance) {
            transferEntry.sendAcceptance = sendAcceptance;
        }
        if (result) {
            transferEntry.result = result;
        }

        buffer = Buffer.from(JSON.stringify(transferEntry));

        await ctx.stub.putState(transferEntryId, buffer);

        if (status === TransferStatus.RESPONDED) {
            ctx.stub.setEvent('transferResponded', buffer);
        }
    }

    @Transaction()
    public async deleteTransferEntry(ctx: Context, transferEntryId: string): Promise<void> {
        const exists = await this.transferEntryExists(ctx, transferEntryId);
        if (!exists) {
            throw new Error(`The transfer entry ${transferEntryId} does not exist`);
        }
        await ctx.stub.deleteState(transferEntryId);
    }

}
