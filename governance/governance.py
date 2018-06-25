from iconservice import *


class Governance(IconScoreBase):

    def __init__(self, db: IconScoreDatabase, addr_owner: Address) -> None:
        super().__init__(db, addr_owner)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def getScoreStatus(self) -> dict:
        result = {
            "next": {
                "status": "pending",
                "deployTxHash": "0xe0f6dc6607aa9b5550cd1e6d57549f67fe9718654cde15258922d0f88ff58b27"
            }
        }
        return result

    @external
    def acceptScore(self, txHash: str):
        pass

    @external
    def rejectScore(self, txHash: str, reason: str):
        pass

    @external
    def selfRevoke(self):
        pass

    @external
    def addAuditor(self, address: Address):
        pass

    @external
    def removeAuditor(self, address: Address):
        pass
