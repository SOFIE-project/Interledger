/*
 * SPDX-License-Identifier: Apache-2.0
 */

import { Object, Property } from 'fabric-contract-api';
import { type } from 'os';

export enum TransferStatus {
    READY = 1,
    INQUIRED,
    ANSWERED,
    SENT,
    RESPONDED,
    CONFIRMING,
    FINALIZED
}

// export type TransferResult = {
//     status: boolean,
//     txHash?: string,
//     exception?: string,
//     errorCode?: number,
//     message?: string,

//     commitStatus?: boolean,
//     commitTxHash?: string,
//     commitErrorCode?: number,
//     commitMessage?: string

//     abortStatus?: boolean,
//     abortTxHash?: string,
//     abortErrorCode?: number,
//     abortMessage?: string
// };

@Object()
export class TransferEntry {

    @Property()
    public status: TransferStatus = TransferStatus.READY;
    public payload?: {
        id: string,
        nonce: string,
        data: string,
    };
    public sendAcceptance?: boolean;
    public result?: string;
}
