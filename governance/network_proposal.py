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


class ApproveCondition:
    APPROVE_VOTE_COUNT = 14
    APPROVE_DELEGATION_RATE = 0.66
    DISAPPROVE_VOTE_COUNT = 7
    DISAPPROVE_DELEGATION_RATE = 0.33


class MaliciousScoreType:
    MIN = 0
    FREEZE = MIN
    UNFREEZE = 1
    MAX = UNFREEZE


class NetworkProposal:
    """ Network Proposal which implements related method, controls DB and make result formatted """
    _PROPOSAL_LIST = 'proposal_list'
    _PROPOSAL_LIST_KEYS = 'proposal_list_keys'

    def __init__(self, db: IconScoreDatabase) -> None:
        self._proposal_list = DictDB(self._PROPOSAL_LIST, db, value_type=bytes)
        self._proposal_list_keys = ArrayDB(self._PROPOSAL_LIST_KEYS, db, value_type=bytes)
        self._validate_func: list = [
            self._validate_text_proposal,
            self._validate_revision_proposal,
            self._validate_malicious_score_proposal,
            self._validate_prep_disqualification_proposal,
            self._validate_step_price_proposal
        ]

    def register_proposal(self, id: bytes, proposer: 'Address', start: int, expired: int,
                          description: str, type: int, value: dict) -> None:
        """ Put transaction hash and info of the proposal to db

        :param id: transaction hash to register the proposal
        :param proposer: address of EOA who want to register the proposal
        :param start: start block height of the proposal
        :param expired: expire block height of the proposal
        :param description: description of the proposal
        :param type: type of the proposal
        :param value: specific value of the proposal
        """
        if not self._validate_proposal(type, value):
            revert("Invalid parameter")

        self._proposal_list_keys.put(id)
        _STATUS = NetworkProposalStatus.VOTING
        _VOTER = {
            "agree": [],
            "disagree": []
        }
        proposal_info = ProposalInfo(id, proposer, description, type, value, start, expired, _STATUS, _VOTER)
        self._proposal_list[id] = proposal_info.to_bytes()

    def cancel_proposal(self, id: bytes, proposer: 'Address', current_block_height: int) -> None:
        """ Set status out of the proposal's info to NetworkProposalStatus.CANCELED

        :param id: transaction hash to cancel the proposal
        :param proposer: address of EOA who want to cancel this proposal
        :param current_block_height: current block height
        """
        if not self._check_registered_proposal(id):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[id])

        if proposal_info.end_block_height < current_block_height:
            revert("This proposal has already expired")

        if proposer != proposal_info.proposer:
            revert("No permission - only for proposer")

        if proposal_info.status != NetworkProposalStatus.VOTING:
            revert("Can not be canceled - only voting proposal")

        proposal_info.status = NetworkProposalStatus.CANCELED
        self._proposal_list[id] = proposal_info.to_bytes()

    def vote_proposal(self, id: bytes, voter: 'Address', vote_type: int, current_block_height: int,
                      main_preps: list) -> (bool, int, dict):
        """ Vote for the proposal - agree or disagree
        
        :param id: transaction hash to vote to the proposal
        :param voter: voter address
        :param vote_type: votes type - agree(NetworkProposalVote.AGREE, 1) or disagree(NetworkProposalVote.DISAGREE, 0)
        :param current_block_height: current block height
        :param main_preps: main prep list having Prep instance
        :return: bool - True means success for voting and False means failure for voting
        """
        if not self._check_registered_proposal(id):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[id])

        if proposal_info.end_block_height < current_block_height:
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

        self._proposal_list[id] = proposal_info.to_bytes()

        return approved, proposal_info.type, proposal_info.value

    def get_proposal(self, id: bytes, current_block_height: int) -> dict:
        """ Get proposal information by ID

        :param id: transaction hash to register the proposal
        :param current_block_height: current block height
        :return: the proposal info in result format in dict
        """
        if not self._check_registered_proposal(id):
            revert("No registered proposal")

        proposal_info = ProposalInfo.from_bytes(self._proposal_list[id])

        if proposal_info.end_block_height < current_block_height:
            if proposal_info.status == NetworkProposalStatus.VOTING:
                proposal_info.status = NetworkProposalStatus.DISAPPROVED

        result = {
            "proposer": proposal_info.proposer,
            "id": proposal_info.id,
            "status": hex(proposal_info.status),
            "startBlockHeight": hex(proposal_info.start_block_height),
            "endBlockHeight": hex(proposal_info.end_block_height),
            "voter": proposal_info.voter,
            "contents": {
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                "value": proposal_info.value
            }
        }

        return result

    def get_proposal_list(self, current_block_height: int) -> dict:
        """ Get proposal list

        :param current_block_height: current block height
        :return: the proposal info list in result format in dict
        """
        proposals = []
        for id in self._proposal_list_keys:
            proposal_info = ProposalInfo.from_bytes(self._proposal_list[id])

            if proposal_info.end_block_height < current_block_height:
                if proposal_info.status == NetworkProposalStatus.VOTING:
                    proposal_info.status = NetworkProposalStatus.DISAPPROVED

            proposal_info_in_dict = {
                "id": proposal_info.id,
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                "status": hex(proposal_info.status),
                "startBlockHeight": hex(proposal_info.start_block_height),
                "endBlockHeight": hex(proposal_info.end_block_height)
            }
            proposals.append(proposal_info_in_dict)

        result = {
            "proposals": proposals
        }
        return result

    def _validate_proposal(self, proposal_type: int, value: dict):
        result = False
        try:
            validator = self._validate_func[proposal_type]
            result = validator(value)
        except Exception as e:
            Logger.error(f"Network proposal parameter validation error :{e}")
        finally:
            return result

    @staticmethod
    def _validate_text_proposal(value: dict) -> bool:
        text = value['text']
        return isinstance(text, str)

    @staticmethod
    def _validate_revision_proposal(value: dict) -> bool:
        code = int(value['code'], 16)
        name = value['name']

        return isinstance(code, int) and isinstance(name, str)

    @staticmethod
    def _validate_malicious_score_proposal(value: dict) -> bool:
        address = Address.from_string(value['address'])
        type_ = int(value['type'], 16)

        return isinstance(address, Address) and address.is_contract \
               and MaliciousScoreType.MIN <= type_ <= MaliciousScoreType.MAX

    @staticmethod
    def _validate_prep_disqualification_proposal(value: dict) -> bool:
        address = Address.from_string(value['address'])

        main_preps, _ = get_main_prep_info()
        sub_preps, _ = get_sub_prep_info()

        for prep in main_preps + sub_preps:
            if prep.address == address:
                return True

        return False

    @staticmethod
    def _validate_step_price_proposal(value: dict) -> bool:
        value = int(value['value'], 16)

        return isinstance(value, int)

    def _check_registered_proposal(self, id: bytes) -> bool:
        """ Check if the proposal with ID have already registered

        :param id: transaction hash to register the proposal
        :return: bool
        """
        proposal_in_bytes = self._proposal_list[id]
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
            if str(prep.address) in preps_to_vote:
                delegated_of_preps_to_vote += prep.delegated

        try:
            if vote_type == NetworkProposalVote.AGREE:
                return len(preps_to_vote) > ApproveCondition.APPROVE_VOTE_COUNT \
                       and delegated_of_preps_to_vote / total_delegated > ApproveCondition.APPROVE_DELEGATION_RATE
            else:
                return len(preps_to_vote) > ApproveCondition.DISAPPROVE_VOTE_COUNT \
                       and delegated_of_preps_to_vote / total_delegated > ApproveCondition.DISAPPROVE_DELEGATION_RATE
        except ZeroDivisionError:
            return False


class ProposalInfo:
    """ ProposalInfo Class including proposal information"""

    def __init__(self, id: bytes, proposer: 'Address', description: str, type: int, value: dict,
                 start_block_height: int, end_block_height: int, status: int, voter: dict):
        self.id = id
        self.proposer = proposer
        self.description = description
        self.type = type
        self.value = value  # value dict has str value
        self.start_block_height = start_block_height
        self.end_block_height = end_block_height
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
