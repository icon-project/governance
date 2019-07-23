import hashlib
import random
import sys
import unittest
from copy import deepcopy
from json import dumps, loads
from unittest.mock import patch, Mock

from iconservice import *
from tbears.libs.scoretest.score_test_case import Address

from governance.network_proposal import NetworkProposal, ProposalInfo, NetworkProposalVote, NetworkProposalStatus, \
    NetworkProposalType


class TestUnitNetworkProposal(unittest.TestCase):

    @patch('governance.network_proposal.ArrayDB', return_value=[])
    @patch('governance.network_proposal.DictDB', return_value={})
    def setUp(self, DictDB, ArrayDB):
        db = Mock()
        db.__class = IconScoreDatabase
        self.network_proposal = NetworkProposal(db)

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    def test_proposal_info_to_bytes_from_bytes(self, json_dumps, json_loads):
        tx_hash = create_tx_hash()
        proposer = create_address()
        description = "Disqualify P-Rep A; P-Rep A does not maintain node"
        type = 3
        value = {
            "address": bytes.hex(Address.to_bytes(create_address()))
        }
        start_block_height = 1
        end_block_height = 10
        status = NetworkProposalStatus.VOTING
        voter = {
            "agree": [str(create_address()), str(create_address())],
            "disagree": [str(create_address())]
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, start_block_height, end_block_height,
                                     status, voter)
        proposal_info_in_bytes = proposal_info.to_bytes()

        expected_value = {
            "id": bytes.hex(tx_hash),
            "proposer": str(proposer),
            "description": "Disqualify P-Rep A; P-Rep A does not maintain node",
            "type": type,
            "value": value,
            "start_block_height": start_block_height,
            "end_block_height": end_block_height,
            "status": status,
            "voter": voter
        }
        self.assertEqual(proposal_info_in_bytes, dumps(expected_value).encode())
        self.assertEqual(proposal_info_in_bytes, proposal_info.from_bytes(proposal_info_in_bytes).to_bytes())

    @patch('governance.network_proposal.NetworkProposal._validate_step_price_proposal', return_value=True)
    @patch('governance.network_proposal.NetworkProposal._validate_prep_disqualification_proposal', return_value=True)
    @patch('governance.network_proposal.NetworkProposal._validate_malicious_score_proposal', return_value=True)
    @patch('governance.network_proposal.NetworkProposal._validate_revision_proposal', return_value=True)
    @patch('governance.network_proposal.NetworkProposal._validate_text_proposal', return_value=True)
    def test_validate_proposal(self, _validate_text_proposal, _validate_revision_proposal,
                               _validate_malicious_score_proposal, _validate_prep_disqualification_proposal,
                               _validate_step_price_proposal):
        value_of_type_0 = {"text": "text"}
        value_of_type_1 = {"code": hex(0), "name": "1.1.0"}
        value_of_type_2 = {"address": str(create_address()), "type": hex(0)}
        value_of_type_3 = {"address": str(create_address())}
        value_of_type_4 = {"value": hex(0)}

        return_value = _validate_text_proposal(0, value_of_type_0)
        assert _validate_text_proposal.called and return_value

        return_value = _validate_text_proposal(1, value_of_type_1)
        assert _validate_text_proposal.called and return_value

        return_value = _validate_text_proposal(2, value_of_type_2)
        assert _validate_text_proposal.called and return_value

        return_value = _validate_text_proposal(3, value_of_type_3)
        assert _validate_text_proposal.called and return_value

        return_value = _validate_text_proposal(4, value_of_type_4)
        assert _validate_text_proposal.called and return_value

    def test_validate_text_proposal(self):
        value_of_type_0 = {"text": "text"}
        assert self.network_proposal._validate_text_proposal(value_of_type_0)

    def test_validate_revision_proposal(self):
        value_of_type_1 = {"code": hex(0), "name": "1.1.0"}
        assert self.network_proposal._validate_revision_proposal(value_of_type_1)

    @patch('governance.network_proposal.Address.is_contract', return_value=True)
    def test_validate_malicious_score_proposal(self, is_contract):
        value_of_type_2 = {"address": str(create_address()), "type": hex(0)}
        assert self.network_proposal._validate_malicious_score_proposal(value_of_type_2)

    def test_validate_prep_disqualification_proposal(self):
        class Prep:
            def __init__(self, address: Address):
                self.address = address

        main_prep = [Prep(create_address()) for i in range(22)]
        sub_prep = [Prep(create_address()) for i in range(22, 100)]

        with patch('governance.network_proposal.get_main_prep_info',
                   return_value=(main_prep, None)) as get_main_prep_info:
            with patch('governance.network_proposal.get_sub_prep_info',
                       return_value=(sub_prep, None)) as get_sub_prep_info:
                value_of_type_3 = {"address": str(main_prep[0].address)}
                assert self.network_proposal._validate_prep_disqualification_proposal(value_of_type_3)
                value_of_type_3 = {"address": str(sub_prep[0].address)}
                assert self.network_proposal._validate_prep_disqualification_proposal(value_of_type_3)
                value_of_type_3 = {"address": str(create_address())}
                assert not self.network_proposal._validate_prep_disqualification_proposal(value_of_type_3)

    def test_validate_step_price_proposal(self):
        value_of_type_4 = {"value": hex(0)}
        assert self.network_proposal._validate_step_price_proposal(value_of_type_4)

    @patch('governance.network_proposal.ArrayDB', return_value=[])
    @patch('governance.network_proposal.DictDB', return_value={})
    def test_check_registered_proposal(self, DictDB, ArrayDB):
        db = Mock()
        db.__class = IconScoreDatabase
        network_proposal = NetworkProposal(db)

        tx_hash = create_tx_hash()
        self.assertRaises(KeyError, network_proposal._check_registered_proposal, tx_hash)

        network_proposal._proposal_list[tx_hash] = create_tx_hash()
        self.assertTrue(network_proposal._check_registered_proposal(tx_hash))

    def test_check_vote_result(self):
        # case(1): return False, when type is 'agree', len(prep) <= 14, delegated >= 66%
        main_preps, preps_to_vote = self._create_preps_to_vote(14, 70)
        self.assertFalse(self._check_vote_result_by_mocking(NetworkProposalVote.AGREE, main_preps, preps_to_vote))

        # case(2): return False, when type is 'agree', len(prep) > 14, delegated < 66%
        main_preps, preps_to_vote = self._create_preps_to_vote(15, 60)
        self.assertFalse(self._check_vote_result_by_mocking(NetworkProposalVote.AGREE, main_preps, preps_to_vote))

        # case(3): return True, when type is 'agree', len(prep) > 14, delegated >= 66%
        main_preps, preps_to_vote = self._create_preps_to_vote(15, 70)
        self.assertTrue(self._check_vote_result_by_mocking(NetworkProposalVote.AGREE, main_preps, preps_to_vote))

        # case(4): return False, when type is 'disagree', len(prep) <= 7, delegated >= 33%
        main_preps, preps_to_vote = self._create_preps_to_vote(7, 40)
        self.assertFalse(self._check_vote_result_by_mocking(NetworkProposalVote.DISAGREE, main_preps, preps_to_vote))

        # case(5): return False, when type is 'disagree', len(prep) > 7, delegated < 33%
        main_preps, preps_to_vote = self._create_preps_to_vote(8, 30)
        self.assertFalse(self._check_vote_result_by_mocking(NetworkProposalVote.DISAGREE, main_preps, preps_to_vote))

        # case(6): return True, when type is 'disagree', len(prep) > 7, delegated >= 33%
        main_preps, preps_to_vote = self._create_preps_to_vote(8, 40)
        self.assertTrue(self._check_vote_result_by_mocking(NetworkProposalVote.DISAGREE, main_preps, preps_to_vote))

    @patch('governance.network_proposal.NetworkProposal._check_registered_proposal', return_value=True)
    def test_get_proposal(self, _check_registered_proposal):
        current_block_height = 11

        tx_hash = create_tx_hash()
        proposer = create_address()
        description = "Disqualify P-Rep A; P-Rep A does not maintain node"
        type = 3
        value = {
            "address": bytes.hex(Address.to_bytes(create_address()))
        }
        start_block_height = 1
        end_block_height = 10
        status = NetworkProposalStatus.VOTING
        voter = {
            "agree": [str(create_address()), str(create_address())],
            "disagree": [str(create_address())]
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, start_block_height, end_block_height,
                                     status, voter)

        expected_value = {
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

        self.network_proposal._proposal_list[tx_hash] = create_tx_hash()

        # case(1): when finish prep period (end block height < current block height), NetworkProposalStatus == VOTING
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        # case(2): when finish prep period (end block height < current block height), NetworkProposalStatus == APPROVED
        proposal_info.status = NetworkProposalStatus.APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.APPROVED)
            self.assertEqual(result, expected_value)

        # case(3): when finish prep period (end block height < current block height),
        # NetworkProposalStatus == DISAPPROVED
        proposal_info.status = NetworkProposalStatus.DISAPPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        # case(4): when finish prep period (end block height < current block height), NetworkProposalStatus == CANCELED
        proposal_info.status = NetworkProposalStatus.CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.CANCELED)
            self.assertEqual(result, expected_value)

        current_block_height = 5
        proposal_info.status = NetworkProposalStatus.VOTING
        # case(5): during prep period (end block height >= current block height), Network proposal status == VOTING
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.VOTING)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.APPROVED
        # case(6): during prep period (end block height >= current block height), Network proposal status == APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.APPROVED)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.DISAPPROVED
        # case(7): during prep period (end block height >= current block height), Network proposal status == DISAPPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.DISAPPROVED)
            self.assertEqual(result, expected_value)

        proposal_info.status = NetworkProposalStatus.CANCELED
        # case(8): during prep period (end block height >= current block height), Network proposal status == CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            result = self.network_proposal.get_proposal(tx_hash, current_block_height)
            expected_value["status"] = hex(NetworkProposalStatus.CANCELED)
            self.assertEqual(result, expected_value)

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    def test_get_proposal_list_during_prep_period(self, json_dumps, json_loads):
        proposal_list_keys = []
        proposal_list = {}
        expected_proposal_list = {
            "proposals": []
        }
        for i in range(5):
            id = create_tx_hash()
            proposal_list_keys.append(id)
            proposal_info, proposal_list[id] = self._get_proposal_info(id, NetworkProposalStatus.VOTING)
            proposal_info_in_dict = {
                "id": id,
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                "status": hex(proposal_info.status),
                "startBlockHeight": hex(proposal_info.start_block_height),
                "endBlockHeight": hex(proposal_info.end_block_height)
            }
            expected_proposal_list["proposals"].append(proposal_info_in_dict)

        with patch('governance.network_proposal.DictDB', return_value=proposal_list):
            with patch('governance.network_proposal.ArrayDB', return_value=proposal_list_keys):
                current_block_height = 5
                db = Mock()
                db.__class = IconScoreDatabase
                self.network_proposal = NetworkProposal(db)
                result = self.network_proposal.get_proposal_list(current_block_height)
                self.assertEqual(expected_proposal_list, result)

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    def test_get_proposal_list_when_finish_prep_period(self, json_dumps, json_loads):
        proposal_list_keys = []
        proposal_list = {}
        expected_proposal_list = {
            "proposals": []
        }
        for i in range(5):
            id = create_tx_hash()
            proposal_list_keys.append(id)
            proposal_info, proposal_list[id] = self._get_proposal_info(id, NetworkProposalStatus.VOTING)
            proposal_info_in_dict = {
                "id": id,
                "description": proposal_info.description,
                "type": hex(proposal_info.type),
                # when end block height < current block height, NetworkProposalStatus should be DISAPPROVED
                "status": hex(NetworkProposalStatus.DISAPPROVED),
                "startBlockHeight": hex(proposal_info.start_block_height),
                "endBlockHeight": hex(proposal_info.end_block_height)
            }
            expected_proposal_list["proposals"].append(proposal_info_in_dict)

        with patch('governance.network_proposal.DictDB', return_value=proposal_list):
            with patch('governance.network_proposal.ArrayDB', return_value=proposal_list_keys):
                current_block_height = 11
                db = Mock()
                db.__class = IconScoreDatabase
                self.network_proposal = NetworkProposal(db)
                result = self.network_proposal.get_proposal_list(current_block_height)
                self.assertEqual(expected_proposal_list, result)

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    @patch('governance.network_proposal.NetworkProposal._validate_proposal', return_value=True)
    @patch('governance.network_proposal.ArrayDB')
    @patch('governance.network_proposal.DictDB', return_value={})
    def test_register_proposal(self, DictDB, ArrayDB, _validate_proposal, json_dumps, json_loads):

        class TmpArrayDB():
            def __init__(self):
                self.id = []

            def put(self, _id):
                self.id.append(_id)
                return self.id

            def __str__(self):
                return self.id

        attrs = {'return_value': TmpArrayDB()}
        ArrayDB.configure_mock(**attrs)

        db = Mock()
        db.__class = IconScoreDatabase
        self.network_proposal = NetworkProposal(db)

        for i in range(5):
            id = create_tx_hash()
            proposer = create_address()
            description = "Disqualify P-Rep A; P-Rep A does not maintain node"
            type = 3
            value = {
                "address": bytes.hex(Address.to_bytes(create_address()))
            }
            start_block_height = 1
            end_block_height = 10
            status = NetworkProposalStatus.VOTING
            voter = {
                "agree": [],
                "disagree": []
            }

            proposal_info = ProposalInfo(id, proposer, description, type, value, start_block_height, end_block_height,
                                         status, voter)
            self.network_proposal.register_proposal(id, proposer, start_block_height, end_block_height, description,
                                                    type, value)
            self.assertEqual(i + 1, len(self.network_proposal._proposal_list))
            self.assertEqual(proposal_info.to_bytes(), self.network_proposal._proposal_list[id])

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    @patch('governance.network_proposal.NetworkProposal._check_registered_proposal', return_value=False)
    def test_cancel_proposal(self, _check_registered_proposal, json_dumps, json_loads):
        current_block_height = 5

        tx_hash = create_tx_hash()
        proposer = create_address()
        description = "Disqualify P-Rep A; P-Rep A does not maintain node"
        type = 3
        value = {
            "address": bytes.hex(Address.to_bytes(create_address()))
        }
        start_block_height = 1
        end_block_height = 10
        status = NetworkProposalStatus.VOTING
        voter = {
            "agree": [str(create_address()), str(create_address())],
            "disagree": [str(create_address())]
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, start_block_height, end_block_height,
                                     status, voter)

        self.network_proposal._proposal_list[tx_hash] = create_tx_hash()

        # case(1): raise revert when not check registered proposal
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No registered proposal", self.network_proposal.cancel_proposal,
                                   tx_hash, proposer, current_block_height)

        # case(2): raise revert when end block height < current block height
        current_block_height = 11
        _check_registered_proposal.return_value = True
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already expired",
                                   self.network_proposal.cancel_proposal,
                                   tx_hash, proposer, current_block_height)

        # case(3): raise revert when proposer is not the proposer who registered the proposal
        current_block_height = 5
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No permission - only for proposer",
                                   self.network_proposal.cancel_proposal,
                                   tx_hash, create_address(), current_block_height)

        # case(4): raise revert when status is not VOTING
        proposal_info.status = NetworkProposalStatus.APPROVED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "Can not be canceled - only voting proposal",
                                   self.network_proposal.cancel_proposal,
                                   tx_hash, proposer, current_block_height)

        # confirmed the correct proposal status is CANCELED
        proposal_info.status = NetworkProposalStatus.VOTING
        proposal_info.proposer = proposer
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.network_proposal.cancel_proposal(tx_hash, proposer, current_block_height)
            proposal_info.status = NetworkProposalStatus.CANCELED
            self.assertEqual(ProposalInfo.from_bytes(self.network_proposal._proposal_list[tx_hash]), proposal_info)

    @patch('governance.network_proposal.json_loads', side_effect=loads)
    @patch('governance.network_proposal.json_dumps', side_effect=dumps)
    @patch('governance.network_proposal.NetworkProposal._check_vote_result', return_value=True)
    @patch('governance.network_proposal.NetworkProposal._check_registered_proposal', return_value=False)
    def test_vote_proposal(self, _check_registered_proposal, _check_vote_result, json_dumps, json_loads):
        current_block_height = 5

        tx_hash = create_tx_hash()
        proposer = create_address()
        description = "Disqualify P-Rep A; P-Rep A does not maintain node"
        type = NetworkProposalType.PREP_DISQUALIFICATION
        value = {
            "address": bytes.hex(Address.to_bytes(create_address()))
        }
        start_block_height = 1
        end_block_height = 10
        status = NetworkProposalStatus.VOTING
        voter_agree = create_address()
        voter_disagree = create_address()
        voter = {
            "agree": [str(voter_agree), str(create_address())],
            "disagree": [str(voter_disagree)]
        }
        proposal_info = ProposalInfo(tx_hash, proposer, description, type, value, start_block_height, end_block_height,
                                     status, voter)

        self.network_proposal._proposal_list[tx_hash] = create_tx_hash()

        # case(1): raise revert when not check registered proposal
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "No registered proposal", self.network_proposal.vote_proposal,
                                   tx_hash, proposer, NetworkProposalVote.AGREE, current_block_height, [])

        # case(2): raise revert when end block height < current block height
        current_block_height = 11
        _check_registered_proposal.return_value = True
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already expired",
                                   self.network_proposal.vote_proposal, tx_hash, proposer, NetworkProposalVote.AGREE,
                                   current_block_height, [])

        # case(3): raise revert status is CANCELED
        current_block_height = 5
        proposal_info.status = NetworkProposalStatus.CANCELED
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            self.assertRaisesRegex(IconScoreException, "This proposal has already canceled",
                                   self.network_proposal.vote_proposal, tx_hash, proposer, NetworkProposalVote.AGREE,
                                   current_block_height, [])

        # case(4): raise revert voter has already voted for agree
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            proposal_info.status = NetworkProposalStatus.APPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_agree, NetworkProposalVote.AGREE,
                                   current_block_height, [])
            proposal_info.status = NetworkProposalStatus.DISAPPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_agree, NetworkProposalVote.AGREE,
                                   current_block_height, [])
            proposal_info.status = NetworkProposalStatus.VOTING
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_agree, NetworkProposalVote.AGREE,
                                   current_block_height, [])

        # case(5): raise revert voter has already voted for disagree
        with patch.object(ProposalInfo, 'from_bytes', return_value=proposal_info):
            proposal_info.status = NetworkProposalStatus.APPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_disagree,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, [])
            proposal_info.status = NetworkProposalStatus.DISAPPROVED
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_disagree,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, [])
            proposal_info.status = NetworkProposalStatus.VOTING
            self.assertRaisesRegex(IconScoreException, "Already voted",
                                   self.network_proposal.vote_proposal, tx_hash, voter_disagree,
                                   NetworkProposalVote.DISAGREE,
                                   current_block_height, [])

        # case(6): when status is VOTING and check vote result is True and vote type is AGREE,
        # check status is APPROVED and return values is correct
        buf_proposal_info = deepcopy(proposal_info)
        with patch.object(ProposalInfo, 'from_bytes', return_value=buf_proposal_info):
            self.assertEqual(buf_proposal_info.status, NetworkProposalStatus.VOTING)
            self.network_proposal._proposal_list[tx_hash] = create_tx_hash()
            buf_voter = create_address()
            approved, proposal_info_type, proposal_info_value = self.network_proposal.vote_proposal(tx_hash,
                                                                                                    buf_voter,
                                                                                                    NetworkProposalVote.AGREE,
                                                                                                    current_block_height,
                                                                                                    [])
            buf_proposal_info.status = NetworkProposalStatus.APPROVED
            buf_proposal_info.voter["agree"].append(str(buf_voter))
            self.assertEqual(ProposalInfo.from_bytes(self.network_proposal._proposal_list[tx_hash]), buf_proposal_info)
            self.assertTrue(approved)
            self.assertEqual(type, proposal_info_type)
            self.assertEqual(value, proposal_info_value)

        # case(7): when status is VOTING and check vote result is True and vote type is DISAGREE,
        # check status is DISAPPROVED and return values is correct
        buf_proposal_info = deepcopy(proposal_info)
        with patch.object(ProposalInfo, 'from_bytes', return_value=buf_proposal_info):
            buf_proposal_info.status = NetworkProposalStatus.VOTING
            self.assertEqual(buf_proposal_info.status, NetworkProposalStatus.VOTING)
            buf_voter = create_address()
            approved, proposal_info_type, proposal_info_value = self.network_proposal.vote_proposal(tx_hash,
                                                                                                    buf_voter,
                                                                                                    NetworkProposalVote.DISAGREE,
                                                                                                    current_block_height,
                                                                                                    [])
            buf_proposal_info.status = NetworkProposalStatus.DISAPPROVED
            buf_proposal_info.voter["disagree"].append(str(buf_voter))
            self.assertEqual(ProposalInfo.from_bytes(self.network_proposal._proposal_list[tx_hash]), buf_proposal_info)
            self.assertFalse(approved)
            self.assertEqual(type, proposal_info_type)
            self.assertEqual(value, proposal_info_value)

    @staticmethod
    def _create_preps_to_vote(count_of_preps_to_vote: int, delegated_rate: int):
        COUNT_OF_MAIN_PREPS = 22
        DEFAULT_DELEGATED = 10
        main_preps, preps_to_vote = [], []
        total_delegated_of_preps_to_vote = 0
        for i in range(count_of_preps_to_vote):
            prep_address: Address = create_address()
            preps_to_vote.append(str(prep_address))
            # append preps to vote on main_preps
            main_preps.append(Prep(prep_address, DEFAULT_DELEGATED))
            total_delegated_of_preps_to_vote += DEFAULT_DELEGATED

        count_of_preps_not_to_vote = COUNT_OF_MAIN_PREPS - count_of_preps_to_vote
        for i in range(count_of_preps_not_to_vote):
            delegated = (100 - delegated_rate) * total_delegated_of_preps_to_vote / (
                    delegated_rate * count_of_preps_not_to_vote)
            main_preps.append(Prep(create_address(), int(delegated)))

        return main_preps, preps_to_vote

    @staticmethod
    def _check_vote_result_by_mocking(vote_type: int, main_preps: list, preps_to_vote: list) -> bool:
        vote_type_key = "agree" if vote_type == NetworkProposalVote.AGREE else "disagree"
        proposal_info = Mock(voter={vote_type_key: preps_to_vote})
        proposal_info.__class = ProposalInfo
        vote_result = NetworkProposal._check_vote_result(vote_type, proposal_info, main_preps)
        return vote_result

    @staticmethod
    def _get_proposal_info(id: bytes, status: int):
        proposer = create_address()
        description = "Disqualify P-Rep A; P-Rep A does not maintain node"
        type = 3
        value = {
            "address": bytes.hex(Address.to_bytes(create_address()))
        }
        start_block_height = 1
        end_block_height = 10
        voter = {
            "agree": [str(create_address()), str(create_address())],
            "disagree": [str(create_address())]
        }
        proposal_info = ProposalInfo(id, proposer, description, type, value, start_block_height,
                                     end_block_height,
                                     status, voter)
        return proposal_info, proposal_info.to_bytes()


DATA_BYTE_ORDER = 'big'  # big endian


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
    def __init__(self, address: Address, delegated: int):
        self.address = address
        self.delegated = delegated
