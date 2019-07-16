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

    def register_proposal(self, tx_hash: bytes, proposer: 'Address', expired: int,
                          description: str, type: int, value: dict) -> None:
        """ Put transaction hash and info of the proposal to db

        :param tx_hash: transaction hash to register the proposal
        :param proposer: address of EOA who want to register the proposal
        :param expired: expire block height of the proposal
        :param description: description of the proposal
        :param type: type of the proposal
        :param value: specific value of the proposal
        """
        self._proposal_list_keys.put(tx_hash)
        _STATUS = NetworkProposalStatus.VOTING
        _VOTER = {
            "agree": [],
            "disagree": []
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, expired, _STATUS, _VOTER)
        self._proposal_list[tx_hash] = proposal_info.to_bytes()

    def cancel_proposal(self, tx_hash: bytes, proposer: 'Address') -> None:
        """ Set status out of the proposal's info to NetworkProposalStatus.CANCELED

        :param tx_hash: transaction hash to cancel the proposal
        :param proposer: address of EOA who want to cancel this proposal
        """
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        if proposer != proposal_info.proposer:
            revert("No permission - only for proposer")

        if proposal_info.status == NetworkProposalStatus.APPROVED:
            revert("Can not be canceled - already approved")

        proposal_info.status = NetworkProposalStatus.CANCELED
        self._proposal_list[tx_hash] = proposal_info.to_bytes()

    def vote_proposal(self, tx_hash: bytes, voter: 'Address', vote_type: int, current_block_height: int,
                      main_preps: list) -> (bool, int, dict):
        """ Vote for the proposal - agree or disagree
        
        :param tx_hash: transaction hash to vote to the proposal
        :param voter: voter address
        :param vote_type: votes type - agree(NetworkProposalVote.AGREE, 1) or disagree(NetworkProposalVote.DISAGREE, 0)
        :param current_block_height: current block height
        :param main_preps: main prep list having Prep instance
        :return: bool - True means success for voting and False means failure for voting
        """
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        # TODO check <= or <
        if proposal_info.expired < current_block_height:
            revert("This proposal has already expired")

        if proposal_info.status == NetworkProposalStatus.CANCELED:
            revert("This proposal has already canceled")

        _VOTE_TYPE_IN_STR = "agree" if vote_type == NetworkProposalVote.AGREE else "disagree"

        if str(voter) in proposal_info.voter["agree"] + proposal_info.voter["disagree"]:
            revert("Already voted")

        proposal_info.voter[_VOTE_TYPE_IN_STR].append(str(voter))

        # set status
        approved = False
        if proposal_info.status == NetworkProposalStatus.VOTING:
            if self._check_vote_result(vote_type, proposal_info, main_preps):
                if vote_type == NetworkProposalVote.AGREE:
                    proposal_info.status = NetworkProposalStatus.APPROVED
                    approved = True
                else:
                    proposal_info.status = NetworkProposalStatus.DISAPPROVED

        self._proposal_list[tx_hash] = proposal_info.to_bytes()

        return approved, proposal_info.type, proposal_info.value

    def get_proposal(self, tx_hash: bytes, current_block_height: int) -> dict:
        """ Get proposal information by tx hash

        :param tx_hash: transaction hash to register the proposal
        :param current_block_height: current block height
        :return: the proposal info in result format in dict
        """
        if not self._check_registered_proposal(tx_hash):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

        # TODO check <= or <
        if proposal_info.expired < current_block_height and proposal_info.status == NetworkProposalStatus.VOTING:
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

    def get_proposal_list(self, current_block_height: int) -> dict:
        """ Get proposal list

        :param current_block_height: current block height
        :return: the proposal info list in result format in dict
        """
        proposals = []
        for tx_hash in self._proposal_list_keys:
            proposal_info = ProposalInfo.from_bytes(self._proposal_list[tx_hash])

            # TODO check <= or <
            if proposal_info.expired < current_block_height and proposal_info.status == NetworkProposalStatus.VOTING:
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

    @staticmethod
    def _check_vote_result(vote_type: int, proposal_info: 'ProposalInfo', main_preps: list) -> bool:
        """ Check that the results of the vote meet the approve or disapprove conditions

        Approved condition
        1. agreeing preps is more than 14
        2. amount of total delegation of agreeing preps is more than 66%

        Disapprove condition
        1. disagreeing preps is more than 7
        2. amount of total delegation of disagreeing preps is more than 33%

        :return: bool
        """
        total_delegated = 0
        delegated_of_preps_to_vote = 0
        preps_to_vote: list = proposal_info.voter["agree" if vote_type == NetworkProposalVote.AGREE else "disagree"]
        for prep in main_preps:
            total_delegated += prep.delegated
            if prep.address in preps_to_vote:
                delegated_of_preps_to_vote += prep.delegated

        try:
            if vote_type == NetworkProposalVote.AGREE:
                return len(preps_to_vote) > 14 and delegated_of_preps_to_vote / total_delegated > 0.66
            else:
                return len(preps_to_vote) > 7 and delegated_of_preps_to_vote / total_delegated > 0.33
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
        self._convert_value_to_json(proposal_info_in_dict["value"])
        return json_dumps(proposal_info_in_dict).encode()

    def from_bytes(self, buf: bytes) -> 'ProposalInfo':
        """ Create ProposalInfo object from bytes

        :param buf: ProposalInfo in bytes
        :return: ProposalInfo object
        """
        proposal_info_in_dict: dict = json_loads(buf.decode())
        proposal_info_in_dict["id"] = bytes.fromhex(proposal_info_in_dict["id"])
        proposal_info_in_dict["proposer"] = Address.from_string(proposal_info_in_dict["proposer"])
        self._convert_value_to_original(proposal_info_in_dict["value"])
        return ProposalInfo(**proposal_info_in_dict)

    @staticmethod
    def _convert_value_to_json(value_to_be_converted: dict):
        """ Convert value in dict to json for serialization

        :param value_to_be_converted: value in dict to be converted
        :return: None
        """
        for key, value in value_to_be_converted.items():
            if isinstance(value, Address):
                value_to_be_converted[key] = str(value)

    @staticmethod
    def _convert_value_to_original(converted_value: dict):
        """ Convert value in dict to original for deserialization

        :param converted_value: converted value in dict
        :return: None
        """
        for key, value in converted_value.items():
            if key == "address" and isinstance(value, str):
                converted_value[key] = Address.from_string(value)
