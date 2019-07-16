from iconservice import *


class NetworkProposalType:
    TEXT = 0
    REVISION = 1
    MALICIOUS_SCORE = 2
    PREP_DISQUALIFICATION = 3
    STEP_PRICE = 4


class NetworkProposalStatus:
    VOTING = 0
    APPROVED = 1
    DISAPPROVED = 2
    CANCELED = 3


class NetworkProposalVote:
    DISAGREE = 0
    AGREE = 1


class NetworkProposal:
    """ Network Proposal which implements related method, controls DB and make result formatted """
    _PROPOSAL_LIST = 'proposal_list'
    _PROPOSAL_LIST_KEYS = 'proposal_list_keys'

    def __init__(self, db: IconScoreDatabase) -> None:
        self._proposal_list = DictDB(self._PROPOSAL_LIST, db, value_type=bytes)
        self._proposal_list_keys = ArrayDB(self._PROPOSAL_LIST_KEYS, db, value_type=bytes)

    def register_proposal(self, tx_hash: bytes, proposer: 'Address', description: str, type: int, value: dict,
                          expired: int) -> None:
        """ Put transaction hash and info of the proposal to db """
        self._proposal_list_keys.put(tx_hash)
        _STATUS = NetworkProposalStatus.VOTING
        _VOTER = {
            "agree": [],
            "disagree": []
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, expired, _STATUS, _VOTER)
        self._proposal_list[tx_hash] = proposal_info.to_bytes()

    def cancel_proposal(self, tx_hash: bytes, proposer: 'Address') -> None:
        """ Set status out of the proposal's info to NetworkProposalStatus.CANCELED"""
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        if not self._check_proposer(tx_hash, proposer):
            revert("No permission - only for proposer")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        if proposal_info.status == NetworkProposalStatus.APPROVED:
            revert("Can nat be canceled - already approved")

        proposal_info.status = NetworkProposalStatus.CANCELED
        self._proposal_list[tx_hash] = proposal_info.to_bytes()

    def vote_proposal(self, tx_hash: bytes, voter: 'Address', vote_type: int, end_block_height_of_term: int,
                      main_preps: list) -> (bool, int, dict):
        """ Vote for the proposal - agree or disagree
        
        :param tx_hash: transaction hash to register the proposal
        :param voter: voter address
        :param vote_type: votes type - agree(NetworkProposalVote.AGREE, 1) or disagree(NetworkProposalVote.DISAGREE, 0)
        :param end_block_height_of_term: end block height of the current term period
        :param main_preps: main prep list having Prep instance
        :return: bool - True means success for voting and False means failure for voting
        """
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        if proposal_info.expired != end_block_height_of_term:
            revert("This proposal has already expired")

        if proposal_info.status == NetworkProposalStatus.CANCELED:
            revert("This proposal has already canceled")

        _VOTE_TYPE_IN_STR = "agree" if vote_type == NetworkProposalVote.AGREE else "disagree"
        _NOT_VOTE_TYPE_IN_STR = "agree" if vote_type == NetworkProposalVote.DISAGREE else "disagree"

        if str(voter) in proposal_info.voter[_NOT_VOTE_TYPE_IN_STR] + proposal_info.voter[_VOTE_TYPE_IN_STR]:
            revert("Already voted")

        proposal_info.voter[_VOTE_TYPE_IN_STR].append(str(voter))

        approved = self._check_approved(proposal_info, main_preps)
        if approved:
            proposal_info.status = NetworkProposalStatus.APPROVED
        self._proposal_list[tx_hash] = proposal_info.to_bytes()

        return approved, proposal_info.type, proposal_info.value

    def get_proposal(self, tx_hash: bytes, end_block_height_of_term: int) -> dict:
        """ Get proposal information by tx hash

        :param tx_hash: transaction hash to register the proposal
        :param end_block_height_of_term: end block height of the current term period
        :return: the proposal info in result format in dict
        """
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        if proposal_info.expired != end_block_height_of_term and proposal_info.status == NetworkProposalStatus.VOTING:
            proposal_info.status = NetworkProposalStatus.DISAPPROVED

        result = {
            "proposer": proposal_info.proposer,
            "id": proposal_info.id,
            "status": hex(proposal_info.status),
            "voter": proposal_info.voter,
            "contents": {
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                "value": str(proposal_info.value)
            }
        }
        return result

    def get_proposal_list(self, end_block_height_of_term: int) -> dict:
        """ Get proposal list

        :param end_block_height_of_term: end block height of the current term period
        :return: the proposal info list in result format in dict
        """
        proposals = []
        for tx_hash in self._proposal_list_keys:
            proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

            if proposal_info.expired != end_block_height_of_term \
                    and proposal_info.status == NetworkProposalStatus.VOTING:
                proposal_info.status = NetworkProposalStatus.DISAPPROVED

            proposal_info_in_dict = {
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                "status": hex(proposal_info.status)
            }
            proposals.append(proposal_info_in_dict)

        result = {
            "proposals": proposals
        }
        return result

    def _check_registered_proposal(self, tx_hash: str) -> bool:
        """ Check if the proposal with tx hash have already registered

        :param tx_hash: transaction hash to register the proposal
        :return: bool
        """
        proposal_in_bytes = self._proposal_list[tx_hash]
        return True if proposal_in_bytes else False

    def _check_proposer(self, tx_hash: str, proposer: 'Address') -> bool:
        """
        Check if msg sender is proposer of the proposal with the tx hash

        This method should be called after calling the method of check registered proposal.
        :param tx_hash: transaction hash to register the proposal
        :param proposer: proposer who makes the proposal initially
        :return: bool
        """
        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])
        return True if proposer == proposal_info.proposer else False

    @staticmethod
    def _check_approved(proposal_info: 'ProposalInfo', main_preps: list) -> bool:
        """ Check if the proposal is approved

        Approved Case
        1. agreeing preps is more than 15
        2. amount of total delegation of agreeing preps is more than 66%

        :return: bool value if the proposal has already been approved or not
        """
        total_delegated = 0
        delegated_of_preps_to_agree = 0
        preps_to_agree: list = proposal_info.voter["agree"]
        for prep in main_preps:
            total_delegated += prep.delegated
            if prep.address in preps_to_agree:
                delegated_of_preps_to_agree += prep.delegated

        try:
            return len(preps_to_agree) >= 15 or delegated_of_preps_to_agree / total_delegated >= 0.66
        except ZeroDivisionError:
            return False


class ProposalInfo:
    """ ProposalInfo Class including proposal information"""

    def __init__(self, id: bytes, proposer: 'Address', description: str, type: int, value: dict, expired: int,
                 status: int, voter: dict):
        self.id = id
        self.proposer = proposer
        self.description = description
        self.type = type
        self.value = value
        self.expired = expired
        self.status = status
        self.voter = voter

    def to_bytes(self) -> bytes:
        """ Convert ProposalInfo to bytes

        :return: ProposalInfo in bytes
        """
        proposal_info_in_dict = vars(self)
        proposal_info_in_dict["id"] = bytes.hex(proposal_info_in_dict["id"])
        proposal_info_in_dict["proposer"] = str(proposal_info_in_dict["proposer"])
        return json_dumps(proposal_info_in_dict).encode()

    @staticmethod
    def from_bytes(buf: bytes) -> 'ProposalInfo':
        """ Create ProposalInfo object from bytes

        :param buf: ProposalInfo in bytes
        :return: ProposalInfo object
        """
        proposal_info_in_dict: dict = json_loads(buf.decode())
        proposal_info_in_dict["id"] = bytes.fromhex(proposal_info_in_dict["id"])
        proposal_info_in_dict["proposer"] = Address.from_string(proposal_info_in_dict["proposer"])
        return ProposalInfo(**proposal_info_in_dict)
