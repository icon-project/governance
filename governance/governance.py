from iconservice import *

TAG = '*** Governance ***'

CURRENT = 'current'
NEXT = 'next'
STATUS = 'status'
DEPLOY_TXHASH = 'deployTxHash'
AUDIT_TXHASH = 'auditTxHash'
VALID_STATUS_KEYS = [STATUS, DEPLOY_TXHASH, AUDIT_TXHASH]

STATUS_PENDING = 'pending'
STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'
STATUS_REJECTED = 'rejected'


class Governance(IconScoreBase):

    _SCORE_STATUS = 'score_status'
    _AUDITOR_LIST = 'auditor_list'

    # TODO: replace with real func
    _MAP_ADDRESS = {
        '0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27': 'cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32',
        '0xe22222222222222250cd1e6d57549f67fe9718654cde15258922d0f88ff58b27': 'cx222222222f5b45bfaea8cff1d8232fbb6122ec32',
    }
    _MAP_TXHASH = {
        'cxb0776ee37f5b45bfaea8cff1d8232fbb6122ec32': '0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27',
        'cx222222222f5b45bfaea8cff1d8232fbb6122ec32': '0xe22222222222222250cd1e6d57549f67fe9718654cde15258922d0f88ff58b27',
    }

    def __init__(self, db: IconScoreDatabase, addr_owner: Address) -> None:
        super().__init__(db, addr_owner)
        self._score_status = DictDB(self._SCORE_STATUS, db, value_type=str, depth=3)
        self._auditor_list = ArrayDB(self._AUDITOR_LIST, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()
        # add genesis into initial auditor
        self._auditor_list.put(Address.from_string('hx' + '0'*40))  # TODO: replace with the real genesis

    def on_update(self) -> None:
        super().on_update()

    def _get_current_status(self, score_address: Address):
        return self._score_status[score_address][CURRENT]

    def _get_next_status(self, score_address: Address):
        return self._score_status[score_address][NEXT]

    @staticmethod
    def _fill_status(db: DictDB):
        count = 0
        status = {}
        for key in VALID_STATUS_KEYS:
            value = db[key]
            if value:
                status[key] = value
                count += 1
        return count, status

    @staticmethod
    def _save_status(db: DictDB, status: dict) -> None:
        Logger.debug(f'_save_status: status="{status}"', TAG)
        for key in VALID_STATUS_KEYS:
            value = status[key]
            if value:
                db[key] = value

    @staticmethod
    def _remove_status(db: DictDB) -> None:
        for key in VALID_STATUS_KEYS:
            value = db[key]
            if value:
                del db[key]

    @external(readonly=True)
    def getScoreStatus(self, address: Address) -> dict:
        tx_hash = self._MAP_TXHASH[str(address)]  # TODO: replace with real func
        if tx_hash is None:
            self.revert('SCORE not found')
        result = {}
        _current = self._get_current_status(address)
        count1, status = self._fill_status(_current)
        if count1 > 0:
            result[CURRENT] = status
        _next = self._get_next_status(address)
        count2, status = self._fill_status(_next)
        if count2 > 0:
            result[NEXT] = status
        if count1 + count2 == 0:
            # there is no status information, build initial status
            status = {
                STATUS: STATUS_PENDING,
                DEPLOY_TXHASH: tx_hash
            }
            result[NEXT] = status
            # self._save_status(_next, status)  # put is not allowed here!
        return result

    @external
    def acceptScore(self, txHash: str):
        # check message sender
        Logger.debug(f'acceptScore: msg.sender = "{self.msg.sender}"', TAG)
        if self.msg.sender not in self._auditor_list:
            self.revert(f'Invalid sender: no permission')
        # check txHash
        # TODO: replace with real func
        if txHash in self._MAP_ADDRESS:
            score_address = Address.from_string(self._MAP_ADDRESS[txHash])
        else:
            self.revert('Invalid txHash')
        Logger.debug(f'acceptScore: score_address = "{score_address}"', TAG)
        # check next: it should be 'pending'
        result = self.getScoreStatus(score_address)
        try:
            next_status = result[NEXT][STATUS]
            if next_status != STATUS_PENDING:
                self.revert(f'Invalid status: next is {next_status}')
        except KeyError:
            self.revert('Invalid status: no next status')
        # next: pending -> null
        _next = self._get_next_status(score_address)
        self._remove_status(_next)
        # current: null -> active
        _current = self._get_current_status(score_address)
        status = {
            STATUS: STATUS_ACTIVE,
            DEPLOY_TXHASH: txHash,
            AUDIT_TXHASH: self.tx.hash
        }
        self._save_status(_current, status)

    @external
    def rejectScore(self, txHash: str, reason: str):
        # check message sender
        Logger.debug(f'acceptScore: msg.sender = "{self.msg.sender}"', TAG)
        if self.msg.sender not in self._auditor_list:
            self.revert(f'Invalid sender: no permission')
        # check txHash
        # TODO: replace with real func
        if txHash in self._MAP_ADDRESS:
            score_address = Address.from_string(self._MAP_ADDRESS[txHash])
        else:
            self.revert('Invalid txHash')
        Logger.debug(f'rejectScore: score_address = "{score_address}", reason = {reason}', TAG)
        # check next: it should be 'pending'
        result = self.getScoreStatus(score_address)
        try:
            next_status = result[NEXT][STATUS]
            if next_status != STATUS_PENDING:
                self.revert(f'Invalid status: next is {next_status}')
        except KeyError:
            self.revert('Invalid status: no next status')
        # next: pending -> rejected
        _next = self._get_next_status(score_address)
        status = {
            STATUS: STATUS_REJECTED,
            DEPLOY_TXHASH: txHash,
            AUDIT_TXHASH: self.tx.hash
        }
        self._save_status(_next, status)

    @external
    def selfRevoke(self):
        pass

    @external
    def addAuditor(self, address: Address):
        pass

    @external
    def removeAuditor(self, address: Address):
        pass
