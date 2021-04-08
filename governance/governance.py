from iconservice import *

TAG = 'Governance'
VERSION = "0.0.1"


# An interface of ChainScore
class ChainInterface(InterfaceScore):

    @interface
    def disableScore(self, address: Address):
        pass

    @interface
    def enableScore(self, address: Address):
        pass

    @interface
    def setRevision(self, code: int):
        pass

    @interface
    def acceptScore(self, txHash: bytes):
        pass

    @interface
    def rejectScore(self, txHash: bytes):
        pass

    @interface
    def blockScore(self, address: Address):
        pass

    @interface
    def unblockScore(self, address: Address):
        pass

    @interface
    def setStepPrice(self, price: int):
        pass

    @interface
    def setStepCost(self, type: str, cost: int):
        pass

    @interface
    def setMaxStepLimit(self, contextType: str, limit: int):
        pass

class Governance(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._governor_db = ArrayDB('governors', db, value_type=Address)
        self._chain_score = self.create_interface_score(ZERO_SCORE_ADDRESS, ChainInterface)

    def on_install(self) -> None:
        super().on_install()
        self._add_governor(self.owner)

    def on_update(self) -> None:
        super().on_update()

    @external
    def disableScore(self, address: Address):
        self._check_sender_is_governor()
        self._chain_score.disableScore(address)

    @external
    def enableScore(self, address: Address):
        self._check_sender_is_governor()
        self._chain_score.enableScore(address)

    @external
    def setRevision(self, code: int):
        self._check_sender_is_governor()
        self._chain_score.setRevision(code)

    @external
    def acceptScore(self, txHash: bytes):
        self._check_sender_is_governor()
        self._chain_score.acceptScore(txHash)

    @external
    def rejectScore(self, txHash: bytes):
        self._check_sender_is_governor()
        self._chain_score.rejectScore(txHash)

    @external
    def blockScore(self, address: Address):
        self._check_sender_is_governor()
        self._chain_score.blockScore(address)

    @external
    def unblockScore(self, address: Address):
        self._check_sender_is_governor()
        self._chain_score.unblockScore(address)

    @external
    def setStepPrice(self, price: int):
        self._check_sender_is_governor()
        self._chain_score.setStepPrice(price)

    @external
    def setStepCost(self, type: str, cost: int):
        self._check_sender_is_governor()
        self._chain_score.setStepCost(type, cost)

    @external
    def setMaxStepLimit(self, contextType: str, limit: int):
        self._check_sender_is_governor()
        self._chain_score.setMaxStepLimit(contextType, limit)

    @external(readonly=True)
    def getGovernors(self) -> list:
        governors = []
        for governor in self._governor_db:
            governors.append(governor)
        return governors

    @external(readonly=True)
    def getVersion(self) -> str:
        return VERSION

    @external
    def addGovernor(self, governor: Address):
        self._check_sender_is_governor()
        if governor in self._governor_db:
            revert("Exist governor", 10)
        self._add_governor(governor)

    @external
    def removeGovernor(self, governor: Address):
        self._check_sender_is_governor()
        if governor not in self._governor_db:
            revert("Not exist governor", 11)
        self._remove_governor(governor)

    def _add_governor(self, governor: Address):
        self._governor_db.put(governor)

    def _remove_governor(self, governor: Address):
        if governor == self.owner:
            revert("Cannot remove score owner in governors_db", 13)

        # get the top value
        top = self._governor_db.pop()
        if top != governor:
            # search and replace with the top value
            for i in range(len(self._governor_db)):
                if self._governor_db[i] == governor:
                    self._governor_db[i] = top
                    break

    def _check_sender_is_governor(self):
        if self.msg.sender not in self._governor_db:
            revert("Not permitted caller", 14)
