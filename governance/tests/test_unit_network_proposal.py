import hashlib
import random
import sys
import unittest
from collections import namedtuple
from copy import deepcopy
from json import dumps, loads
from unittest.mock import patch, Mock

from iconservice import *
from iconservice.iconscore.icon_score_context_util import IconScoreContextUtil

from governance.governance import Governance
from governance.network_proposal import NetworkProposal, ProposalInfo, NetworkProposalVote, NetworkProposalStatus, \
    NetworkProposalType

DATA_BYTE_ORDER = 'big'  # big endian
COUNT_OF_MAIN_PREPS = 22
DEFAULT_DELEGATED = 10
STEP_PRICE = 100

PATCHER_ARRAY_DB = patch('governance.governance.ArrayDB')
PATCHER_DICT_DB = patch('governance.governance.DictDB')
PATCHER_VAR_DB = patch('governance.governance.VarDB')
PATCHER_VALIDATE_PROPOSAL = patch(
    'governance.governance.Governance._validate_network_proposal', return_value=True)
PATCHER_VALIDATE_TEXT_PROPOSAL = patch(
    'governance.governance.Governance._validate_text_proposal', return_value=True)
PATCHER_VALIDATE_REVISION_PROPOSAL = patch(
    'governance.governance.Governance._validate_revision_proposal', return_value=True)
PATCHER_VALIDATE_MALICIOUS_SCORE_PROPOSAL =patch(
    'governance.governance.Governance._validate_malicious_score_proposal', return_value=True)
PATCHER_VALIDATE_PREP_DISQUALIFICATION_PROPOSAL = patch(
    'governance.governance.Governance._validate_prep_disqualification_proposal', return_value=True)
PATCHER_VALIDATE_STEP_PRICE_PROPOSAL = patch(
    'governance.governance.Governance._validate_step_price_proposal', return_value=True)
PATCHER_VALIDATE_IREP_PROPOSAL = patch(
    'governance.governance.Governance._validate_irep_proposal', return_value=True)
PATCHER_VALIDATE_REWARD_FUND_SETTING_PROPOSAL = patch(
    'governance.governance.Governance._validate_reward_fund_setting_proposal', return_value=True)
PATCHER_VALIDATE_REWARD_FUND_ALLOCATION_PROPOSAL = patch(
    'governance.governance.Governance._validate_reward_fund_allocation_proposal', return_value=True)

PATCHER_NP_ARRAY_DB = patch('governance.network_proposal.ArrayDB')
PATCHER_NP_DICT_DB = patch('governance.network_proposal.DictDB')
PATCHER_JSON_LOADS = patch('governance.network_proposal.json_loads', side_effect=loads)
PATCHER_JSON_DUMPS = patch('governance.network_proposal.json_dumps', side_effect=dumps)
PATCHER_CHECK_VOTE_RESULT = patch('governance.network_proposal.NetworkProposal._check_vote_result', return_value=True)
PATCHER_CHECK_REGISTERED_PROPOSAL = patch(
    'governance.network_proposal.NetworkProposal._check_registered_proposal', return_value=False)


def create_tx_hash(data: bytes = None) -> bytes:
    if data is None:
        max_int = sys.maxsize
        length = (max_int.bit_length() + 7) // 8
        data = int(random.randint(0, max_int)).to_bytes(length, DATA_BYTE_ORDER)
    return hashlib.sha3_256(data).digest()


def create_address(prefix: int = 0, data: bytes = None) -> 'Address':
    if data is None:
        data = create_tx_hash()
    hash_value = hashlib.sha3_256(data).digest()
    return Address(AddressPrefix(prefix), hash_value[-20:])


def start_patches(*args):
    for patcher in args:
        patcher.start()


def stop_patches(*args):
    for patcher in args:
        patcher.stop()


def patch_several(*decorate_args):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_patches(*decorate_args)
            ret = func(*args, **kwargs)
            stop_patches(*decorate_args)
            return ret

        return wrapper

    return decorate


class Prep:
    def __init__(self, address: 'Address', delegated: int):
        self.address = address
        self.delegated = delegated
        self.name = "name_" + str(address)


# @unittest.skip("skip governance SCORE")
class TestUnitGovernance(unittest.TestCase):

    @patch_several(PATCHER_ARRAY_DB, PATCHER_DICT_DB, PATCHER_VAR_DB, PATCHER_NP_ARRAY_DB, PATCHER_NP_DICT_DB)
    def setUp(self) -> None:
        self.owner = Address.from_string(f"cx{'0'*40}")

        db = Mock(spec=IconScoreDatabase)
        db.configure_mock(address=f"cx{'0'*40}")
        IconScoreContextUtil.get_owner = Mock(return_value=self.owner)

        self.governance = Governance(db)

    @patch_several(PATCHER_VALIDATE_TEXT_PROPOSAL, PATCHER_VALIDATE_REVISION_PROPOSAL,
                   PATCHER_VALIDATE_MALICIOUS_SCORE_PROPOSAL, PATCHER_VALIDATE_PREP_DISQUALIFICATION_PROPOSAL,
                   PATCHER_VALIDATE_STEP_PRICE_PROPOSAL, PATCHER_VALIDATE_IREP_PROPOSAL,
                   PATCHER_VALIDATE_REWARD_FUND_SETTING_PROPOSAL, PATCHER_VALIDATE_REWARD_FUND_ALLOCATION_PROPOSAL)
    def test_validate_network_proposal(self):
        for invalid_vote_type in (6, 7, -1, 1000):
            tmp_value = {}
            self.assertFalse(self.governance._validate_network_proposal(invalid_vote_type, tmp_value))

        value_of_type_0 = {"value": "text"}
        value_of_type_1 = {"code": hex(0), "name": "1.1.0"}
        value_of_type_2 = {"address": str(create_address()), "type": hex(0)}
        value_of_type_3 = {"address": str(create_address())}
        value_of_type_4 = {"value": hex(0)}
        value_of_type_5 = {"value": hex(0)}

        return_value = self.governance._validate_network_proposal(0, value_of_type_0)
        assert self.governance._validate_text_proposal.called and return_value

        return_value = self.governance._validate_network_proposal(1, value_of_type_1)
        assert self.governance._validate_revision_proposal.called and return_value

        return_value = self.governance._validate_network_proposal(2, value_of_type_2)
        assert self.governance._validate_malicious_score_proposal.called and return_value

        return_value = self.governance._validate_network_proposal(3, value_of_type_3)
        assert self.governance._validate_prep_disqualification_proposal.called and return_value

        return_value = self.governance._validate_network_proposal(4, value_of_type_4)
        assert self.governance._validate_step_price_proposal.called and return_value

        return_value = self.governance._validate_network_proposal(5, value_of_type_5)
        assert self.governance._validate_irep_proposal.called and return_value

        value_of_type_6 = {"iglobal": hex(0)}
        return_value = self.governance._validate_network_proposal(6, value_of_type_6)
        assert self.governance._validate_reward_fund_setting_proposal.called and return_value

        value_of_type_7 = {"iprep": hex(50), "icps": hex(0), "irelay": hex(0), "ivoter": hex(50)}
        return_value = self.governance._validate_network_proposal(7, value_of_type_7)
        assert self.governance._validate_reward_fund_allocation_proposal.called and return_value

    def test_validate_text_proposal(self):
        value_of_type_0 = {"value": "text"}
        assert self.governance._validate_text_proposal(value_of_type_0)

    def test_validate_revision_proposal(self):
        value_of_type_1 = {"code": hex(0), "name": "1.1.0"}
        assert self.governance._validate_revision_proposal(value_of_type_1)

    @patch('governance.governance.Address.is_contract', return_value=True)
    def test_validate_malicious_score_proposal(self, is_contract):
        value_of_type_2 = {"address": str(create_address(AddressPrefix.CONTRACT)), "type": hex(0)}
        assert self.governance._validate_malicious_score_proposal(value_of_type_2)

    def test_validate_prep_disqualification_proposal(self):
        main_prep = [Prep(create_address(), 0) for _ in range(COUNT_OF_MAIN_PREPS)]
        sub_prep = [Prep(create_address(), 0) for _ in range(COUNT_OF_MAIN_PREPS, 100)]

        with patch('governance.governance.get_main_prep_info', return_value=(main_prep, None)):
            with patch('governance.governance.get_sub_prep_info', return_value=(sub_prep, None)):
                value_of_type_3 = {"address": str(main_prep[0].address)}
                assert self.governance._validate_prep_disqualification_proposal(value_of_type_3)
                value_of_type_3 = {"address": str(sub_prep[0].address)}
                assert self.governance._validate_prep_disqualification_proposal(value_of_type_3)
                value_of_type_3 = {"address": str(create_address())}
                assert not self.governance._validate_prep_disqualification_proposal(value_of_type_3)

    @patch('governance.governance.Governance.get_icon_network_value', return_value=STEP_PRICE)
    def test_validate_step_price_proposal(self,  get_icon_network_value):
        TestCase = namedtuple("TestCase", "step_price, result")
        tests = [
            TestCase(STEP_PRICE + 1, True),
            TestCase(STEP_PRICE - 1, True),
            TestCase(STEP_PRICE * 125 // 100, True),
            TestCase(STEP_PRICE * 127 // 100, False),
            TestCase(STEP_PRICE * 75 // 100, True),
            TestCase(STEP_PRICE * 74 // 100, False),
        ]

        for i, test in enumerate(tests):
            value_of_type_4 = {"value": hex(test.step_price)}
            assert test.result == self.governance._validate_step_price_proposal(value_of_type_4), f"#{i+1}: {test.step_price}"
            value_of_type_4 = {"value": str(test.step_price)}
            assert test.result == self.governance._validate_step_price_proposal(value_of_type_4), f"#{i+1}: {test.step_price}"

    @patch('governance.governance.Governance.validate_irep', return_value=True)
    def test_validate_irep_proposal(self, validate_irep):
        value_of_type_5 = {"value": hex(10)}
        assert self.governance._validate_irep_proposal(value_of_type_5)

    def test_validate_reward_fund_allocation_proposal(self):
        TestCase = namedtuple("TestCase", "iprep, icps, irelay, ivoter, result")
        tests = [
            TestCase(0, 0, 0, 100, True),
            TestCase(25, 25, 25, 25, True),
            TestCase(10, 10, 10, 80, False),
            TestCase(10, 10, 10, 10, False),
            TestCase(-10, 10, 50, 50, False),
        ]

        for i, test in enumerate(tests):
            value_of_type_7 = {
                "iprep": hex(test.iprep),
                "icps": hex(test.icps),
                "irelay": hex(test.irelay),
                "ivoter": hex(test.ivoter),
            }
            assert test.result == self.governance._validate_reward_fund_allocation_proposal(value_of_type_7), f"#{i+1}"


class TestUnitNetworkProposal(unittest.TestCase):

    @patch_several(PATCHER_NP_ARRAY_DB, PATCHER_NP_DICT_DB)
    def setUp(self) -> None:
        db = Mock()
        db.__class = IconScoreDatabase
        self.network_proposal = NetworkProposal(db)
        self.network_proposal._proposal_list = {}
        self.network_proposal._proposal_list_keys = []

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_proposal_info_to_bytes_from_bytes(self):
        total_voter: int = 22
        total_delegated_amount: int = 3000
        vote = self._generate_vote(1, 100, 2, 200, total_delegated_amount, total_voter)
        proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
            NetworkProposalStatus.VOTING, vote)
        proposal_info_in_bytes = proposal_info.to_bytes()

        expected_value = {
            "id": proposal_info.id,
            "proposer": str(proposal_info.proposer),
            "proposer_name": proposal_info.proposer_name,
            "title": proposal_info.title,
            "description": proposal_info.description,
            "type": proposal_info.type,
            "value": proposal_info.value,
            "start_block_height": proposal_info.start_block_height,
            "end_block_height": proposal_info.end_block_height,
            "status": proposal_info.status,
            "vote": vote,
            "total_voter": total_voter,
            "total_delegated_amount": total_delegated_amount
        }

        self.assertEqual(proposal_info_in_bytes, dumps(expected_value).encode())
        self.assertEqual(proposal_info_in_bytes, proposal_info.from_bytes(proposal_info_in_bytes).to_bytes())

    def test_validate_proposal_type(self):
        for valid_proposal_type in (0, 1, 2, 3, 4, 5, 6, 7):
            self.assertTrue(self.network_proposal._validate_proposal_type(valid_proposal_type))
        for invalid_proposal_type in (8, 9, -1, 1000):
            self.assertFalse(self.network_proposal._validate_proposal_type(invalid_proposal_type))

    def test_validate_proposal_status(self):
        for valid_proposal_status in (0, 1, 2, 3):
            self.assertTrue(self.network_proposal._validate_proposal_status(valid_proposal_status))
        for invalid_proposal_status in (4, 5, 6, 7, -1, 1000):
            self.assertFalse(self.network_proposal._validate_proposal_status(invalid_proposal_status))

    def test_validate_vote_type(self):
        for valid_vote_type in (0, 1):
            self.assertTrue(self.network_proposal._validate_vote_type(valid_vote_type))
        for invalid_vote_type in (2, 3, 4, 5, 6, 7, -1, 1000):
            self.assertFalse(self.network_proposal._validate_vote_type(invalid_vote_type))

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_check_registered_proposal(self):
        tx_hash = create_tx_hash()
        self.assertRaises(KeyError, self.network_proposal._check_registered_proposal, tx_hash)

        self.network_proposal._proposal_list[tx_hash] = create_tx_hash()
        self.assertTrue(self.network_proposal._check_registered_proposal(tx_hash))

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_check_vote_result(self):
        # case(1): return False, when type is 'agree', len(prep) < 15, delegated >= 66%
        vote = self._generate_vote(14, 66, 0, 0, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.AGREE, proposal_info))

        # case(2): return False, when type is 'agree', len(prep) >= 15, delegated < 66%
        vote = self._generate_vote(15, 65, 0, 0, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.AGREE, proposal_info))

        # case(3): return True, when type is 'agree', len(prep) >= 15, delegated >= 66%
        vote = self._generate_vote(15, 66, 0, 0, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertTrue(self.network_proposal._check_vote_result(NetworkProposalVote.AGREE, proposal_info))

        # case(4): return False, when type is 'disagree', len(prep) < 8, delegated >= 33%
        vote = self._generate_vote(0, 0, 7, 33, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.DISAGREE, proposal_info))

        # case(5): return False, when type is 'disagree', len(prep) >= 8, delegated < 33%
        vote = self._generate_vote(0, 0, 8, 32, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.DISAGREE, proposal_info))

        # case(6): return True, when type is 'disagree', len(prep) >= 8, delegated >= 33%
        vote = self._generate_vote(0, 0, 8, 33, 100)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertTrue(self.network_proposal._check_vote_result(NetworkProposalVote.DISAGREE, proposal_info))

        # case(7): return True, when type is 'agree', len(prep) >= 3, delegated >= 66%, total_voter = 4
        vote = self._generate_vote(3, 66, 0, 0, 100, 4)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertTrue(self.network_proposal._check_vote_result(NetworkProposalVote.AGREE, proposal_info))

        # case(8): return False, when type is 'agree', len(prep) = 2, delegated >= 66%, total_voter = 4
        vote = self._generate_vote(2, 66, 0, 0, 100, 4)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.AGREE, proposal_info))

        # case(9): return True, when type is 'disagree', len(prep) = 2, delegated >= 33%, total_voter = 4
        vote = self._generate_vote(0, 0, 2, 33, 100, 4)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertTrue(self.network_proposal._check_vote_result(NetworkProposalVote.DISAGREE, proposal_info))

        # case(10): return False, when type is 'disagree', len(prep) = 2, delegated < 33%, total_voter = 4
        vote = self._generate_vote(0, 0, 2, 32, 100, 4)
        proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, vote)
        self.assertFalse(self.network_proposal._check_vote_result(NetworkProposalVote.DISAGREE, proposal_info))

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS, PATCHER_CHECK_REGISTERED_PROPOSAL)
    def test_get_proposal(self):
        voter = self._generate_vote(2, 10, 3, 20, 100)
        proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
            NetworkProposalStatus.VOTING, voter)
        current_block_height = proposal_info.end_block_height + 1

        buf_proposal_info = deepcopy(proposal_info)
        expected_value = self.network_proposal._generate_proposal_info_in_dict_for_get_proposal(buf_proposal_info)

        self.network_proposal._check_registered_proposal.return_value = True
        # case(1): when finish prep period (end block height < current block height), NetworkProposalStatus == VOTING
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        # case(2): when finish prep period (end block height < current block height), NetworkProposalStatus == APPROVED
        proposal_info.status = NetworkProposalStatus.APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.APPROVED)
            self.assertEqual(result, expected_value)

        # case(3): when finish prep period (end block height < current block height),
        # NetworkProposalStatus == DISAPPROVED
        proposal_info.status = NetworkProposalStatus.DISAPPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        # case(4): when finish prep period (end block height < current block height), NetworkProposalStatus == CANCELED
        proposal_info.status = NetworkProposalStatus.CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.CANCELED)
            self.assertEqual(result, expected_value)

        current_block_height = proposal_info.end_block_height - 1
        proposal_info.status = NetworkProposalStatus.VOTING
        # case(5): during prep period (end block height >= current block height), Network proposal status == VOTING
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.VOTING)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.APPROVED
        # case(6): during prep period (end block height >= current block height), Network proposal status == APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.APPROVED)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.DISAPPROVED
        # case(7): during prep period (end block height >= current block height), Network proposal status == DISAPPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.CANCELED
        # case(8): during prep period (end block height >= current block height), Network proposal status == CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(proposal_info)):
            result = self.network_proposal.get_proposal(proposal_info.id, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.CANCELED)
            self.assertEqual(result, expected_value)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_get_proposals_during_prep_period(self):
        expected_proposal_list = {
            "proposals": []
        }
        voter = self._generate_vote(2, 10, 3, 20, 100)

        for i in range(5):
            proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
                NetworkProposalStatus.VOTING, voter)
            self.network_proposal._proposal_list_keys.append(proposal_info.id)
            proposal_info_in_dict = self.network_proposal._generate_proposal_info_in_dict_for_get_proposals(
                proposal_info)
            expected_proposal_list["proposals"].append(proposal_info_in_dict)

        current_block_height = proposal_info.end_block_height - 1
        result = self.network_proposal.get_proposals(current_block_height)
        self.assertEqual(expected_proposal_list, result)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_get_proposal_list_when_finish_prep_period(self):
        expected_proposal_list = {
            "proposals": []
        }
        voter = self._generate_vote(2, 10, 3, 20, 100)

        for i in range(5):
            proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
                NetworkProposalStatus.VOTING, voter)
            self.network_proposal._proposal_list_keys.append(proposal_info.id)

            buf_proposal_info = deepcopy(proposal_info)
            buf_proposal_info.status = NetworkProposalStatus.DISAPPROVED
            buf_proposal_info_in_dict = self.network_proposal._generate_proposal_info_in_dict_for_get_proposals(
                buf_proposal_info)
            expected_proposal_list["proposals"].append(buf_proposal_info_in_dict)

            current_block_height = proposal_info.end_block_height + 1
            result = self.network_proposal.get_proposals(current_block_height)

            self.assertEqual(expected_proposal_list, result)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_get_proposal_list_when_filter_by_type(self):
        for i in range(5):
            expected_proposal_list = {
                "proposals": []
            }
            voter = self._generate_vote(2, 10, 3, 20, 100)
            buf_network_proposal_type = [
                NetworkProposalType.TEXT, NetworkProposalType.REVISION, NetworkProposalType.MALICIOUS_SCORE,
                NetworkProposalType.PREP_DISQUALIFICATION, NetworkProposalType.STEP_PRICE
            ]
            proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
                NetworkProposalStatus.VOTING, voter, buf_network_proposal_type[i])
            self.network_proposal._proposal_list_keys.append(proposal_info.id)

            buf_proposal_info_in_dict = self.network_proposal._generate_proposal_info_in_dict_for_get_proposals(
                proposal_info)
            expected_proposal_list["proposals"].append(buf_proposal_info_in_dict)

            current_block_height = proposal_info.end_block_height - 1
            result = self.network_proposal.get_proposals(current_block_height, buf_network_proposal_type[i])
            self.assertEqual(i + 1, len(self.network_proposal._proposal_list))
            self.assertEqual(expected_proposal_list, result)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_get_proposal_list_when_filter_by_status(self):
        for i in range(4):
            expected_proposal_list = {
                "proposals": []
            }
            voter = self._generate_vote(2, 10, 3, 20, 100)
            buf_network_proposal_type = [
                NetworkProposalType.TEXT, NetworkProposalType.REVISION, NetworkProposalType.MALICIOUS_SCORE,
                NetworkProposalType.PREP_DISQUALIFICATION, NetworkProposalType.STEP_PRICE
            ]
            buf_network_proposal_status = [
                NetworkProposalStatus.VOTING, NetworkProposalStatus.APPROVED,
                NetworkProposalStatus.DISAPPROVED, NetworkProposalStatus.CANCELED
            ]
            proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
                buf_network_proposal_status[i], voter, buf_network_proposal_type[i])
            self.network_proposal._proposal_list_keys.append(proposal_info.id)

            buf_proposal_info_in_dict = self.network_proposal._generate_proposal_info_in_dict_for_get_proposals(
                proposal_info)
            expected_proposal_list["proposals"].append(buf_proposal_info_in_dict)

            current_block_height = proposal_info.end_block_height - 1
            result = self.network_proposal.get_proposals(current_block_height, None, buf_network_proposal_status[i])
            self.assertEqual(i + 1, len(self.network_proposal._proposal_list))
            self.assertEqual(expected_proposal_list, result)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS)
    def test_get_proposal_list_when_filter_by_both_type_and_status(self):
        expected_proposal_list = {
            "proposals": []
        }
        for i in range(5):
            voter = self._generate_vote(2, 10, 3, 20, 100)
            buf_network_proposal_type = [
                NetworkProposalType.TEXT, NetworkProposalType.REVISION, NetworkProposalType.REVISION,
                NetworkProposalType.PREP_DISQUALIFICATION, NetworkProposalType.STEP_PRICE
            ]
            proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
                NetworkProposalStatus.VOTING, voter, buf_network_proposal_type[i])
            self.network_proposal._proposal_list_keys.append(proposal_info.id)

            buf_proposal_info_in_dict = self.network_proposal._generate_proposal_info_in_dict_for_get_proposals(
                proposal_info)

            if proposal_info.type == NetworkProposalType.REVISION:
                expected_proposal_list["proposals"].append(buf_proposal_info_in_dict)

        current_block_height = proposal_info.end_block_height - 1
        result = self.network_proposal.get_proposals(current_block_height, NetworkProposalType.REVISION,
                                                     NetworkProposalStatus.VOTING)
        self.assertEqual(2, len(result['proposals']))
        self.assertEqual(5, len(self.network_proposal._proposal_list))
        self.assertEqual(expected_proposal_list, result)

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS, PATCHER_NP_ARRAY_DB, PATCHER_NP_DICT_DB)
    def test_register_proposal(self):

        class TmpArrayDB():
            def __init__(self):
                self.id = []

            def put(self, _id):
                self.id.append(_id)
                return self.id

            def __str__(self):
                return self.id

        attrs = {'return_value': TmpArrayDB()}
        self.network_proposal._proposal_list_keys = Mock()
        self.network_proposal._proposal_list_keys.configure_mock(**attrs)

        voter = self._generate_vote(0, 0, 0, 0, DEFAULT_DELEGATED * COUNT_OF_MAIN_PREPS)
        for i in range(5):
            proposal_info, _ = self._generate_proposal_info(NetworkProposalStatus.VOTING, voter)
            voter["noVote"]["list"][i] = str(proposal_info.proposer)
            main_preps = [Prep(Address.from_string(address), DEFAULT_DELEGATED) for address in voter["noVote"]["list"]]
            self.network_proposal.register_proposal(proposal_info.id, proposal_info.proposer,
                                                    proposal_info.start_block_height, proposal_info.end_block_height,
                                                    proposal_info.title, proposal_info.description,
                                                    proposal_info.type, proposal_info.value,
                                                    main_preps)
            self.assertEqual(i + 1, len(self.network_proposal._proposal_list))
            self.assertEqual(self.network_proposal._proposal_list[proposal_info.id], proposal_info.to_bytes())

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS, PATCHER_CHECK_REGISTERED_PROPOSAL)
    def test_cancel_proposal(self):
        voter = self._generate_vote(1, DEFAULT_DELEGATED, 2, DEFAULT_DELEGATED, 100)
        proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
            NetworkProposalStatus.VOTING, voter)
        current_block_height = proposal_info.end_block_height - 1

        # case(1): raise revert when not check registered proposal
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No registered proposal", self.network_proposal.cancel_proposal,
                                   proposal_info.id, proposal_info.proposer, current_block_height)

        # case(2): raise revert when end block height < current block height
        current_block_height = proposal_info.end_block_height + 1
        self.network_proposal._check_registered_proposal.return_value = True
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already expired",
                                   self.network_proposal.cancel_proposal,
                                   proposal_info.id, proposal_info.proposer, current_block_height)

        # case(3): raise revert when proposer is not the proposer who registered the proposal
        current_block_height = proposal_info.end_block_height - 1
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No permission - only for proposer",
                                   self.network_proposal.cancel_proposal,
                                   proposal_info.id, create_address(), current_block_height)

        # case(4): raise revert when status is not VOTING
        proposal_info.status = NetworkProposalStatus.APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "Can not be canceled - only voting proposal",
                                   self.network_proposal.cancel_proposal,
                                   proposal_info.id, proposal_info.proposer, current_block_height)

        # confirmed the correct proposal status is CANCELED
        proposal_info.status = NetworkProposalStatus.VOTING
        proposal_info.proposer = proposal_info.proposer
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            id = proposal_info.id
            self.network_proposal.cancel_proposal(proposal_info.id, proposal_info.proposer, current_block_height)
            proposal_info.status = NetworkProposalStatus.CANCELED
            self.assertEqual(proposal_info, ProposalInfo.from_bytes(self.network_proposal._proposal_list[id]))

    @patch_several(PATCHER_JSON_LOADS, PATCHER_JSON_DUMPS, PATCHER_CHECK_VOTE_RESULT, PATCHER_CHECK_REGISTERED_PROPOSAL)
    def test_vote_proposal(self):
        voter = self._generate_vote(3, DEFAULT_DELEGATED, 2, DEFAULT_DELEGATED,
                                    DEFAULT_DELEGATED * COUNT_OF_MAIN_PREPS)
        address_of_voter_agreeing = voter["agree"]["list"][0]["address"]
        address_of_voter_disagreeing = voter["disagree"]["list"][0]["address"]
        proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
            NetworkProposalStatus.VOTING, voter)
        current_block_height = proposal_info.end_block_height - 1

        buf_timestamp = 10
        # case(1): raise revert when not check registered proposal
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No registered proposal", self.network_proposal.vote_proposal,
                                   proposal_info.id, proposal_info.proposer, NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

        # case(2): raise revert when end block height < current block height
        current_block_height = proposal_info.end_block_height + 1
        self.network_proposal._check_registered_proposal.return_value = True
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already expired",
                                   self.network_proposal.vote_proposal, proposal_info.id, proposal_info.proposer,
                                   NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

        # case(3): raise revert status is CANCELED
        current_block_height = proposal_info.end_block_height - 1
        proposal_info.status = NetworkProposalStatus.CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already canceled",
                                   self.network_proposal.vote_proposal, proposal_info.id, proposal_info.proposer,
                                   NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

        # case(4): raise revert voter has already voted for agree
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            proposal_info.status = NetworkProposalStatus.APPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_agreeing,
                                   NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])
            proposal_info.status = NetworkProposalStatus.DISAPPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_agreeing,
                                   NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])
            proposal_info.status = NetworkProposalStatus.VOTING
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_agreeing,
                                   NetworkProposalVote.AGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

        # case(5): raise revert voter has already voted for disagree
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            proposal_info.status = NetworkProposalStatus.APPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_disagreeing,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])
            proposal_info.status = NetworkProposalStatus.DISAPPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_disagreeing,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])
            proposal_info.status = NetworkProposalStatus.VOTING
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, proposal_info.id, address_of_voter_disagreeing,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

            # case: raise revert voter is not main P-Rep when registered this network proposal
            self.assertRaisesRegex(IconScoreException,
                                   "No permission - only for main prep when network proposal registered",
                                   self.network_proposal.vote_proposal, proposal_info.id, "hx1234",
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, create_tx_hash(), buf_timestamp, [])

        # case(6): when status is VOTING and check vote result is True and vote type is AGREE,
        # check status is APPROVED and return values is correct
        buf_proposal_info = deepcopy(proposal_info)
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(buf_proposal_info)):
            self.assertEqual(buf_proposal_info.status, NetworkProposalStatus.VOTING)
            self.network_proposal._proposal_list[proposal_info.id] = create_tx_hash()
            buf_voter_address = voter["noVote"]["list"][0]
            buf_prep_of_voter_address = Prep(buf_voter_address, DEFAULT_DELEGATED * 2)
            buf_id = create_tx_hash()
            buf_voter_item_in_dict = self.network_proposal._generate_voter_in_dict(buf_id, buf_timestamp,
                                                                                   buf_prep_of_voter_address)

            voter_all_types = [voter_item["address"] for voter_item in
                               voter["agree"]["list"] + voter["disagree"]["list"]]
            voter_all_types += voter["noVote"]["list"]

            main_preps = [Prep(address, DEFAULT_DELEGATED if address != buf_voter_address else DEFAULT_DELEGATED * 2)
                          for address in voter_all_types]
            approved, proposal_info_type, proposal_info_value = self.network_proposal.vote_proposal(proposal_info.id,
                                                                                                    buf_voter_address,
                                                                                                    NetworkProposalVote.AGREE,
                                                                                                    current_block_height,
                                                                                                    buf_id,
                                                                                                    buf_timestamp,
                                                                                                    main_preps)

            buf_proposal_info.status = NetworkProposalStatus.APPROVED
            buf_proposal_info.vote["agree"]["list"].append(buf_voter_item_in_dict)
            buf_proposal_info.vote["agree"]["amount"] += DEFAULT_DELEGATED * 2
            buf_proposal_info.vote["noVote"]["list"].remove(buf_voter_item_in_dict["address"])
            buf_proposal_info.vote["noVote"]["amount"] -= DEFAULT_DELEGATED * 2
            self.assertEqual(self.network_proposal._proposal_list[proposal_info.id], buf_proposal_info.to_bytes())
            self.assertTrue(approved)
            self.assertEqual(proposal_info.type, proposal_info_type)
            self.assertEqual(proposal_info.value, proposal_info_value)

        # case(7): when status is VOTING and check vote result is True and vote type is DISAGREE,
        # check status is DISAPPROVED and return values is correct
        buf_proposal_info = deepcopy(proposal_info)
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(buf_proposal_info)):
            buf_proposal_info.status = NetworkProposalStatus.VOTING
            self.assertEqual(buf_proposal_info.status, NetworkProposalStatus.VOTING)

            buf_voter_address = voter["noVote"]["list"][0]
            buf_prep_of_voter_address = Prep(buf_voter_address, DEFAULT_DELEGATED * 2)
            buf_id = create_tx_hash()
            buf_voter_item_in_dict = self.network_proposal._generate_voter_in_dict(buf_id, buf_timestamp,
                                                                                   buf_prep_of_voter_address)

            voter_all_types = [voter_item["address"] for voter_item in
                               voter["agree"]["list"] + voter["disagree"]["list"]]
            voter_all_types += voter["noVote"]["list"]

            main_preps = [Prep(address, DEFAULT_DELEGATED if address != buf_voter_address else DEFAULT_DELEGATED * 2)
                          for address in voter_all_types]
            approved, proposal_info_type, proposal_info_value = self.network_proposal.vote_proposal(proposal_info.id,
                                                                                                    buf_voter_address,
                                                                                                    NetworkProposalVote.DISAGREE,
                                                                                                    current_block_height,
                                                                                                    buf_id,
                                                                                                    buf_timestamp,
                                                                                                    main_preps)

            buf_proposal_info.status = NetworkProposalStatus.DISAPPROVED
            buf_proposal_info.vote["disagree"]["list"].append(buf_voter_item_in_dict)
            buf_proposal_info.vote["disagree"]["amount"] += DEFAULT_DELEGATED * 2
            buf_proposal_info.vote["noVote"]["list"].remove(buf_voter_item_in_dict["address"])
            buf_proposal_info.vote["noVote"]["amount"] -= DEFAULT_DELEGATED * 2
            self.assertEqual(self.network_proposal._proposal_list[proposal_info.id], buf_proposal_info.to_bytes())
            self.assertFalse(approved)
            self.assertEqual(proposal_info.type, proposal_info_type)
            self.assertEqual(proposal_info.value, proposal_info_value)

        # case(8): when status is VOTING and last voter votes to DISAGREE and check vote result is False,
        # check status is DISAPPROVED and return values is correct
        new_voter = self._generate_vote(3, DEFAULT_DELEGATED * 3, 0, 0, DEFAULT_DELEGATED * 6, 4)
        proposal_info, self.network_proposal._proposal_list[proposal_info.id] = self._generate_proposal_info(
            NetworkProposalStatus.VOTING, new_voter)
        current_block_height = proposal_info.end_block_height - 1

        buf_proposal_info = deepcopy(proposal_info)
        with patch.object(ProposalInfo, 'from_bytes', return_value=deepcopy(buf_proposal_info)):
            buf_proposal_info.status = NetworkProposalStatus.VOTING
            self.assertEqual(buf_proposal_info.status, NetworkProposalStatus.VOTING)

            buf_voter_address = new_voter["noVote"]["list"][0]
            buf_prep_of_voter_address = Prep(buf_voter_address, DEFAULT_DELEGATED * 3)
            buf_id = create_tx_hash()
            buf_voter_item_in_dict = self.network_proposal._generate_voter_in_dict(buf_id, buf_timestamp,
                                                                                   buf_prep_of_voter_address)

            voter_all_types = [voter_item["address"] for voter_item in
                               new_voter["agree"]["list"] + new_voter["disagree"]["list"]]
            voter_all_types += new_voter["noVote"]["list"]

            main_preps = [Prep(address, DEFAULT_DELEGATED if address != buf_voter_address else DEFAULT_DELEGATED * 3)
                          for address in voter_all_types]
            approved, proposal_info_type, proposal_info_value = self.network_proposal.vote_proposal(proposal_info.id,
                                                                                                    buf_voter_address,
                                                                                                    NetworkProposalVote.DISAGREE,
                                                                                                    current_block_height,
                                                                                                    buf_id,
                                                                                                    buf_timestamp,
                                                                                                    main_preps)

            buf_proposal_info.status = NetworkProposalStatus.DISAPPROVED
            buf_proposal_info.vote["disagree"]["list"].append(buf_voter_item_in_dict)
            buf_proposal_info.vote["disagree"]["amount"] += DEFAULT_DELEGATED * 3
            buf_proposal_info.vote["noVote"]["list"].remove(buf_voter_item_in_dict["address"])
            buf_proposal_info.vote["noVote"]["amount"] -= DEFAULT_DELEGATED * 3
            self.assertEqual(self.network_proposal._proposal_list[proposal_info.id], buf_proposal_info.to_bytes())
            self.assertFalse(approved)
            self.assertEqual(proposal_info.type, proposal_info_type)
            self.assertEqual(proposal_info.value, proposal_info_value)

    def _generate_vote(self, cnt_agree_voter: int, delegated_agree_voter: int, cnt_disagree_voter: int,
                       delegated_disagree_voter: int, total_delegated: int,
                       total_voter: int = COUNT_OF_MAIN_PREPS) -> dict:
        vote = {
            "agree": {
                "list": [self._generate_vote_item_in_dict() for _ in range(cnt_agree_voter)],
                "amount": delegated_agree_voter
            },
            "disagree": {
                "list": [self._generate_vote_item_in_dict() for _ in range(cnt_disagree_voter)],
                "amount": delegated_disagree_voter
            },
            "noVote": {
                "list": [str(create_address()) for _ in
                         range(total_voter - cnt_agree_voter - cnt_disagree_voter)],
                "amount": total_delegated - delegated_agree_voter - delegated_disagree_voter
            }
        }
        return vote

    @staticmethod
    def _generate_vote_item_in_dict(timestamp=10, amount=10) -> dict:
        """ Generate one of items in dict of voter list

        :return: voter information in dict; one of the items in dict for voter list.
                 A data type is either integer or string in order not to be converted but to JSON dumps directly
        """
        address = str(create_address())
        voter_in_dict = {
            "id": '0x' + bytes.hex(create_tx_hash()),
            "timestamp": timestamp,
            "address": address,
            "name": "prep_name_" + address,
            "amount": amount
        }
        return voter_in_dict

    @staticmethod
    def _generate_proposal_info(status: int, vote: dict, type: int = NetworkProposalType.MALICIOUS_SCORE) \
            -> ('ProposalInfo', bytes):
        id = create_tx_hash()
        proposer = create_address()
        proposer_name = "name_" + str(proposer)
        title = "title_" + bytes.hex(id)
        description = "description_" + bytes.hex(id)
        value = {
            "address": str(create_address())
        }
        start_block_height = 1
        end_block_height = start_block_height + 9
        proposal_info = ProposalInfo(id, proposer, proposer_name, title, description, type, value, start_block_height,
                                     end_block_height, status, vote)
        buf_proposal_info = deepcopy(proposal_info)
        return proposal_info, buf_proposal_info.to_bytes()
