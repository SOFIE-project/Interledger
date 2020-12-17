from enum import Enum


class TransferStatus(Enum):
    """State of a data transfer during the protocol
    """
    READY = 1
    INQUIRED = 2
    ANSWERED = 3
    SENT = 4
    RESPONDED = 5
    CONFIRMING = 6
    FINALIZED = 7


class Transfer(object):
    """The information paired to a data transfer: its 'future' async call to accept(); the 'result' of the accept();
    the transfer 'state'; the event transfer 'data'.
    """

    def __init__(self):
        self.status = TransferStatus.READY
        self.payload = None  # transactional bundle, {id, nonce, data}
        # denote whether the send task has been accepted by an IL Node
        self.send_accepted = False
        self.send_task = None
        # denote whether the confirm task has been accepted by an IL Node
        self.confirm_accepted = False
        self.confirm_task = None
        self.result = {}


class TransferToMulti(Transfer):
    """The information of a data transfer, that is aimed to for multi-ledger targets
    """

    def __init__(self):
        super().__init__()
        self.inquiry_tasks = None
        self.inquiry_results = None
        self.inquiry_decision = None
        self.send_tasks = None
        self.results = None
