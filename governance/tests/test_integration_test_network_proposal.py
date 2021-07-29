import copy
import json
import os
import time
from typing import Dict, Union, List

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder, TransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice.base.type_converter_templates import ConstantKeys
from iconservice.icon_constant import Revision, PRepStatus
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

from governance.governance import STEP_TYPE_CONTRACT_CALL, STEP_TYPE_CONTRACT_CREATE, STEP_TYPE_GET
from governance.network_proposal import NetworkProposalType, NetworkProposalVote, NetworkProposalStatus, \
    MaliciousScoreType

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))
GOVERNANCE_ADDRESS = f"cx{'0' * 39}1"
DEFAULT_STEP_LIMIT = 1_000_000
DEFAULT_NID = 3


class TestNetworkProposal(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    INIT_GOVERNANCE = os.path.abspath(os.path.join(DIR_PATH, 'data/governance_0_0_6.zip'))

    def setUp(self):
        super().setUp(block_confirm_interval=1, network_only=True)
        # super().setUp()

        self.icon_service = None
        # if you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

    def _get_block_height(self) -> int:
        block_height: int = 0
        if self.icon_service:
            block = self.icon_service.get_block("latest")
            block_height = block['height']
        return block_height

    def _make_blocks(self, to: int):
        block_height = self._get_block_height()

        while to > block_height:
            self.process_confirm_block_tx(self.icon_service)
            block_height += 1

    def _make_blocks_to_next_term(self) -> int:
        iiss_info = self._get_iiss_info()
        next_term = int(iiss_info.get('nextPRepTerm', 0), 16)
        if next_term == 0:
            next_term = int(iiss_info.get('nextCalculation', 0), 16)

        self._make_blocks(to=next_term)

        # wait finishing term calculation
        time.sleep(0.5)

        self.assertEqual(next_term, self._get_block_height())
        return next_term

    def _get_iiss_info(self) -> dict:
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .method("getIISSInfo") \
            .build()
        response = self.process_call(call, self.icon_service)
        return response

    def _update_governance_score(self, content: str = SCORE_PROJECT) -> dict:
        tx_result = self._deploy_score(GOVERNANCE_ADDRESS, content)
        return tx_result

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, content: str = SCORE_PROJECT) -> dict:
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(content)) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result, tx_result)
        self.assertEqual(1, tx_result['status'], tx_result)
        self.assertTrue('scoreAddress' in tx_result, tx_result)

        return tx_result

    def _set_revision(self, code: int, name: str):
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("setRevision") \
            .params({"code": code, "name": name}) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        return tx_result

    @staticmethod
    def _create_transfer_icx_tx(key_wallet: 'KeyWallet',
                                to_: str,
                                value: int,
                                step_limit: int = DEFAULT_STEP_LIMIT,
                                nid: int = DEFAULT_NID,
                                nonce: int = 0) -> 'Transaction':
        transaction = TransactionBuilder() \
            .from_(key_wallet.get_address()) \
            .to(to_) \
            .value(value) \
            .step_limit(step_limit) \
            .nid(nid) \
            .nonce(nonce) \
            .build()

        signed_transaction = SignedTransaction(transaction, key_wallet)

        return signed_transaction

    def _create_register_prep_tx(self,
                                 key_wallet: 'KeyWallet',
                                 reg_data: Dict[str, Union[str, bytes]] = None,
                                 value: int = 2000000000000000000000,
                                 step_limit: int = DEFAULT_STEP_LIMIT,
                                 nid: int = DEFAULT_NID,
                                 nonce: int = 0) -> 'SignedTransaction':
        if not reg_data:
            reg_data = self._create_register_prep_params(key_wallet)

        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(SCORE_INSTALL_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("registerPRep"). \
            params(reg_data). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)

        return signed_transaction

    @staticmethod
    def _create_register_prep_params(key_wallet: 'KeyWallet') -> Dict[str, Union[str, bytes]]:
        name = f"node{key_wallet.get_address()}"

        return {
            ConstantKeys.NAME: name,
            ConstantKeys.COUNTRY: "KOR",
            ConstantKeys.CITY: "Unknown",
            ConstantKeys.EMAIL: f"{name}@example.com",
            ConstantKeys.WEBSITE: f"https://{name}.example.com",
            ConstantKeys.DETAILS: f"https://{name}.example.com/details",
            ConstantKeys.P2P_ENDPOINT: f"{name}.example.com:7100",
        }

    def _create_register_prep_tx_list(self, preps: List['KeyWallet']) -> List['SignedTransaction']:
        register_prep_tx_list = []
        for prep in preps:
            register_prep_tx_list.append(self._create_register_prep_tx(prep))

        return register_prep_tx_list

    @staticmethod
    def _create_unregister_prep_tx(key_wallet: 'KeyWallet',
                                   value: int = 0,
                                   step_limit: int = DEFAULT_STEP_LIMIT,
                                   nid: int = DEFAULT_NID,
                                   nonce: int = 0) -> 'SignedTransaction':
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(SCORE_INSTALL_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("unregisterPRep"). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)

        return signed_transaction

    @staticmethod
    def _create_stake_tx(key_wallet: 'KeyWallet',
                         stake: int,
                         value: int = 0,
                         step_limit: int = DEFAULT_STEP_LIMIT,
                         nid: int = DEFAULT_NID,
                         nonce: int = 0) -> 'SignedTransaction':
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(SCORE_INSTALL_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("setStake"). \
            params({"value": hex(stake)}). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)
        return signed_transaction

    @staticmethod
    def _create_delegation_tx(key_wallet: 'KeyWallet',
                              delegations: List[dict],
                              value: int = 0,
                              step_limit: int = DEFAULT_STEP_LIMIT,
                              nid: int = DEFAULT_NID,
                              nonce: int = 0) -> 'SignedTransaction':
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(SCORE_INSTALL_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("setDelegation"). \
            params({"delegations": delegations}). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)
        return signed_transaction

    @staticmethod
    def _create_register_proposal_tx(key_wallet: 'KeyWallet',
                                     title: str,
                                     desc: str,
                                     type: int,
                                     value_dict: dict,
                                     value: int = 0,
                                     step_limit: int = DEFAULT_STEP_LIMIT,
                                     nid: int = DEFAULT_NID,
                                     nonce: int = 0) -> 'SignedTransaction':
        params = {
            "title": title,
            "description": desc,
            "type": hex(type),
            "value": "0x" + bytes.hex(json.dumps(value_dict).encode())
        }
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(GOVERNANCE_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("registerProposal"). \
            params(params). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)
        return signed_transaction

    @staticmethod
    def _create_vote_proposal_tx(key_wallet: 'KeyWallet',
                                 id_: str,
                                 vote: int,
                                 value: int = 0,
                                 step_limit: int = DEFAULT_STEP_LIMIT,
                                 nid: int = DEFAULT_NID,
                                 nonce: int = 0) -> 'SignedTransaction':
        params = {
            "id": id_,
            "vote": hex(vote)
        }
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(GOVERNANCE_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("voteProposal"). \
            params(params). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)
        return signed_transaction

    @staticmethod
    def _create_cancel_proposal_tx(key_wallet: 'KeyWallet',
                                   id_: str,
                                   value: int = 0,
                                   step_limit: int = DEFAULT_STEP_LIMIT,
                                   nid: int = DEFAULT_NID,
                                   nonce: int = 0) -> 'SignedTransaction':
        params = {
            "id": id_,
        }
        transaction = CallTransactionBuilder(). \
            from_(key_wallet.get_address()). \
            to(GOVERNANCE_ADDRESS). \
            value(value). \
            step_limit(step_limit). \
            nid(nid). \
            nonce(nonce). \
            method("cancelProposal"). \
            params(params). \
            build()

        signed_transaction = SignedTransaction(transaction, key_wallet)
        return signed_transaction

    def get_revision(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("getRevision") \
            .build()
        return self.process_call(call, self.icon_service)

    def get_network_proposal(self, id_: str):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("getProposal") \
            .params({"id": id_}) \
            .build()
        return self.process_call(call, self.icon_service)

    def get_step_price(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("getStepPrice") \
            .build()
        return self.process_call(call, self.icon_service)

    def get_irep(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("getIRep") \
            .build()
        return self.process_call(call, self.icon_service)

    def get_main_preps(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .method("getMainPReps") \
            .build()
        response = self.process_call(call, self.icon_service)
        return response

    def get_step_costs(self):
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("getStepCosts") \
            .build()
        return self.process_call(call, self.icon_service)

    def test_001_init_integration_test(self):
        response = self.get_revision()
        if isinstance(response['code'], str):
            code = int(response['code'], 16)
        else:
            code = 0

        # update governance SCORE & revision, if necessary
        if code < Revision.DECENTRALIZATION.value:
            # deploy initial governance SCORE
            self._update_governance_score(self.INIT_GOVERNANCE)

            # enable IISS
            self._set_revision(Revision.IISS.value, "enable IISS")

            # enable decentralization
            response = self._set_revision(Revision.DECENTRALIZATION.value, "enable decentralization")
            self.assertTrue('status' in response, response)
            self.assertEqual(1, response['status'], response)

            # update governance SCORE
            self._update_governance_score(SCORE_PROJECT)

        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .method("getPReps") \
            .build()
        response = self.process_call(call, self.icon_service)

        # register 22 P-Reps
        preps = [self._test1] + self._wallet_array[0:21]
        if len(response.get('preps', [])) < 22:
            tx_list = self._create_register_prep_tx_list(preps)
            response = self.process_transaction_bulk(tx_list, self.icon_service)
            for i, resp in enumerate(response):
                self.assertTrue('status' in resp,
                                f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
                self.assertEqual(1, resp['status'],
                                 f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")

            # stake and delegate
            # min delegation amount = 0.02 * total supply
            delegate_value = self.icon_service.get_total_supply() * 2 // 1000
            stake_value = delegate_value * 2

            tx_list = []
            for i, prep in enumerate(preps):
                # stake
                tx_list.append(self._create_stake_tx(prep, stake_value))

                # delegate
                if i == 0:
                    delegate = delegate_value * 2
                else:
                    delegate = delegate_value

                tx_list.append(self._create_delegation_tx(prep,
                                                          [{"address": prep.get_address(), "value": hex(delegate)}]))

            # process TX with bulk
            response = self.process_transaction_bulk(tx_list, self.icon_service)
            for i, resp in enumerate(response):
                self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
                self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")

            # go to next P-Rep term for main P-Rep election
            self._make_blocks_to_next_term()

        # get main P-Rep
        response = self.get_main_preps()
        self.assertEqual(22, len(response['preps']), response)

    def test_010_manage_network_proposal(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'test proposal'
        value = 'hello world'
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.TEXT, {"value": value})
        response = self.process_transaction(tx, self.icon_service)
        self.assertTrue('status' in response and 1 == response['status'],
                        f"TX:\n{tx.signed_transaction_dict}\nTX_RESULT:\n{response}")
        np_id = response['txHash']
        # check event log
        event_log = response['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('NetworkProposalRegistered(str,str,int,bytes,Address)', event_log['indexed'][0], event_log)
        self.assertEqual(title, event_log['data'][0], event_log)
        self.assertEqual(desc, event_log['data'][1], event_log)
        self.assertEqual(hex(NetworkProposalType.TEXT), event_log['data'][2], event_log)
        self.assertEqual(proposer.get_address(), event_log['data'][4], event_log)
        # check proposal
        response = self.get_network_proposal(np_id)
        self.assertEqual(proposer.get_address(), response['proposer'], response)
        self.assertEqual(np_id, response['id'], response)
        self.assertEqual(desc, response['contents']['description'], response)
        self.assertEqual(hex(NetworkProposalType.TEXT), response['contents']['type'], response)
        self.assertEqual(value, response['contents']['value']['value'], response)

        # vote - agree
        tx = self._create_vote_proposal_tx(proposer, np_id, NetworkProposalVote.AGREE)
        response = self.process_transaction(tx, self.icon_service)
        # check event log
        event_log = response['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('NetworkProposalVoted(bytes,int,Address)', event_log['indexed'][0], event_log)
        self.assertEqual(np_id, event_log['data'][0], event_log)
        self.assertEqual(hex(NetworkProposalVote.AGREE), event_log['data'][1], event_log)
        self.assertEqual(proposer.get_address(), event_log['data'][2], event_log)
        # check proposal
        response = self.get_network_proposal(np_id)
        self.assertTrue(proposer.get_address() in response['vote']['agree']['list'][0]["address"])

        # vote - disagree
        tx = self._create_vote_proposal_tx(self._wallet_array[0], np_id, NetworkProposalVote.DISAGREE)
        response = self.process_transaction(tx, self.icon_service)
        # check event log
        event_log = response['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('NetworkProposalVoted(bytes,int,Address)', event_log['indexed'][0], event_log)
        self.assertEqual(np_id, event_log['data'][0], event_log)
        self.assertEqual(hex(NetworkProposalVote.DISAGREE), event_log['data'][1], event_log)
        self.assertEqual(self._wallet_array[0].get_address(), event_log['data'][2], event_log)
        # check proposal
        response = self.get_network_proposal(np_id)
        self.assertTrue(self._wallet_array[0].get_address() in response['vote']['disagree']['list'][0]["address"],
                        response)

        # cancel proposal
        tx = self._create_cancel_proposal_tx(proposer, np_id)
        response = self.process_transaction(tx, self.icon_service)
        # check event log
        event_log = response['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('NetworkProposalCanceled(bytes)', event_log['indexed'][0], event_log)
        self.assertEqual(np_id, event_log['data'][0], event_log)
        # check proposal
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.CANCELED), response['status'], response)

        # vote to canceled proposal
        tx = self._create_vote_proposal_tx(self._wallet_array[1], np_id, NetworkProposalVote.AGREE)
        response = self.process_transaction(tx, self.icon_service)
        self.assertTrue("status" in response, response)
        self.assertEqual(0, response['status'], response)
        response = self.get_network_proposal(np_id)
        self.assertFalse(self._wallet_array[1].get_address() in response['vote']['agree']['list'][0]["address"],
                         response)

        # TEST: register I-Rep proposal before revision update
        proposer = self._test1
        title = "test title"
        desc = 'irep network proposal'
        irep_current = int(self.get_irep(), 16)
        irep = irep_current + irep_current // 10
        value = {"value": hex(irep)}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.IREP, value)
        response = self.process_transaction(tx, self.icon_service)
        self.assertEqual(0, response['status'], response)

    def test_020_approve_network_proposal(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'test proposal'
        value = 'hello world'
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.TEXT, {"value": value})
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 65%)
        tx_list = []
        for prep in self._wallet_array[0:15]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.VOTING), response['status'], response)

        # vote - agree (16, 74%)
        tx = self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)
        response = self.process_transaction(tx, self.icon_service)
        # check event log
        event_log = response['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('NetworkProposalApproved(bytes)', event_log['indexed'][0], event_log)
        self.assertEqual(np_id, event_log['data'][0], event_log)
        # check status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'test proposal'
        value = 'hello world'
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.TEXT, {"value": value})
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (14, 65%)
        tx_list.clear()
        tx_list.append(self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE))
        for prep in self._wallet_array[0:13]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.VOTING), response['status'], response)

        # vote - agree (15, 69%)
        tx = self._create_vote_proposal_tx(self._wallet_array[13], np_id, NetworkProposalVote.AGREE)
        self.process_transaction(tx, self.icon_service)
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # vote to approved network proposal
        tx = self._create_vote_proposal_tx(self._wallet_array[14], np_id, NetworkProposalVote.AGREE)
        response = self.process_transaction(tx, self.icon_service)
        self.assertTrue("status" in response, response)
        self.assertEqual(1, response['status'], response)
        response = self.get_network_proposal(np_id)
        self.assertTrue(self._wallet_array[14].get_address() in response['vote']['agree']['list'][-1]["address"],
                        response)

    def test_030_disapprove_network_proposal(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'test proposal'
        value = 'hello world'
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.TEXT, {"value": value})
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - disagree (7, 30%)
        tx_list = []
        for prep in self._wallet_array[0:7]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.DISAGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.VOTING), response['status'], response)

        # vote - disagree (8, 34%)
        tx = self._create_vote_proposal_tx(self._wallet_array[7], np_id, NetworkProposalVote.DISAGREE)
        self.process_transaction(tx, self.icon_service)
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.DISAPPROVED), response['status'], response)

        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'test proposal'
        value = 'hello world'
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.TEXT, {"value": value})
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - disagree (7, 34%)
        tx_list.clear()
        tx_list.append(self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.DISAGREE))
        for prep in self._wallet_array[0:6]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.DISAGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.VOTING), response['status'], response)

        # vote - disagree (8, 39%)
        tx = self._create_vote_proposal_tx(self._wallet_array[6], np_id, NetworkProposalVote.DISAGREE)
        self.process_transaction(tx, self.icon_service)
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.DISAPPROVED), response['status'], response)

        # vote to disapproved network proposal
        tx = self._create_vote_proposal_tx(self._wallet_array[7], np_id, NetworkProposalVote.AGREE)
        response = self.process_transaction(tx, self.icon_service)
        self.assertTrue("status" in response, response)
        self.assertEqual(1, response['status'], response)
        response = self.get_network_proposal(np_id)
        self.assertTrue(self._wallet_array[7].get_address() in response['vote']['agree']['list'][-1]["address"],
                        response)

    def test_040_revision_update(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'revision update network proposal'
        code = Revision.SET_IREP_VIA_NETWORK_PROPOSAL.value # for irep NP test
        name = "for revision update network proposal test"
        value = {"code": hex(code), "name": name}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.REVISION, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('RevisionChanged(int,str)', event_log['indexed'][0], event_log)
        self.assertEqual(hex(code), event_log['data'][0], event_log)
        self.assertEqual(name, event_log['data'][1], event_log)
        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # get revision
        response = self.get_revision()
        self.assertEqual(hex(code), response['code'])
        self.assertEqual(name, response['name'])

    def test_050_malicious_score(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal - freeze SCORE
        proposer = self._test1
        title = "test title"
        desc = 'Malicious SCORE network proposal'
        address = f"cxa23{'0' * 37}"
        value = {"address": address, "type": hex(MaliciousScoreType.FREEZE)}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.MALICIOUS_SCORE, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('MaliciousScore(Address,int)', event_log['indexed'][0], event_log)
        self.assertEqual(address, event_log['data'][0], event_log)
        self.assertEqual(hex(MaliciousScoreType.FREEZE), event_log['data'][1], event_log)
        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # check SCORE blacklist
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("isInScoreBlackList") \
            .params({"address": address}) \
            .build()
        response = self.process_call(call, self.icon_service)
        self.assertEqual("0x1", response, response)

        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal - unfreeze SCORE
        proposer = self._test1
        title = "test title"
        desc = 'Unfreeze malicious SCORE network proposal'
        value = {"address": address, "type": hex(MaliciousScoreType.UNFREEZE)}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.MALICIOUS_SCORE, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('MaliciousScore(Address,int)', event_log['indexed'][0], event_log)
        self.assertEqual(address, event_log['data'][0], event_log)
        self.assertEqual(hex(MaliciousScoreType.UNFREEZE), event_log['data'][1], event_log)
        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # check SCORE blacklist
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(GOVERNANCE_ADDRESS) \
            .method("isInScoreBlackList") \
            .params({"address": address}) \
            .build()
        response = self.process_call(call, self.icon_service)
        self.assertEqual("0x0", response, response)

    def test_060_prep_disqualification(self):
        # register new P-Rep for disqualification
        new_prep = self._make_new_prep()

        # register proposal - P-Rep disqualification
        proposer = self._test1
        title = "test title"
        desc = 'P-Rep disqualification network proposal'
        value = {"address": new_prep.get_address()}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.PREP_DISQUALIFICATION, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")

        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('PRepDisqualified(Address,bool,str)', event_log['indexed'][0], event_log)
        self.assertEqual(new_prep.get_address(), event_log['data'][0], event_log)
        self.assertEqual('0x1', event_log['data'][1], event_log)
        self.assertEqual('', event_log['data'][2], event_log)

        # check network proposal approved
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # check P-Rep disqualification
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .method("getPRep") \
            .params({"address": new_prep.get_address()}) \
            .build()
        response = self.process_call(call, self.icon_service)
        self.assertEqual(hex(PRepStatus.DISQUALIFIED.value), response['status'], response)

    def _make_new_prep(self) -> KeyWallet:
        new_prep = KeyWallet.create()

        # transfer ICX to new P-Rep
        tx = self._create_transfer_icx_tx(self._test1, new_prep.get_address(), 2000000000000000000000 * 2)
        response = self.process_transaction(tx, self.icon_service)
        self.assertTrue('status' in response, f"TX:\n{tx.signed_transaction_dict}\nTX_RESULT:\n{response}")

        tx_list = []

        # register new P-Rep
        tx_list.append(self._create_register_prep_tx(new_prep))

        # delegate to new P-Rep
        tx_list.append(self._create_stake_tx(new_prep, 1000))
        tx_list.append(self._create_delegation_tx(new_prep,
                                                  [{"address": new_prep.get_address(), "value": hex(1000)}]))

        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")

        # go to next P-Rep term for P-Rep election
        self._make_blocks_to_next_term()

        return new_prep

    def test_061_prep_disqualification_failed(self):
        # register new P-Rep for disqualification
        new_prep = self._make_new_prep()

        # register proposal - P-Rep disqualification
        proposer = self._test1
        title = "test title"
        desc = 'P-Rep disqualification network proposal'
        value = {"address": new_prep.get_address()}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.PREP_DISQUALIFICATION, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # unregister disqualification target
        tx_list = [self._create_unregister_prep_tx(new_prep)]

        # vote - agree (15, 69%)
        tx_list.append(self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE))
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")

        # check disqualification event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('PRepDisqualified(Address,bool,str)', event_log['indexed'][0], event_log)
        self.assertEqual(new_prep.get_address(), event_log['data'][0], event_log)
        self.assertEqual('0x0', event_log['data'][1], event_log)
        self.assertTrue(event_log['data'][2].startswith(f'Inactive P-Rep: {new_prep.get_address()}'), event_log)

        # check approved
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # check P-Rep disqualification
        call = CallBuilder() \
            .from_(self._test1.get_address()) \
            .to(SCORE_INSTALL_ADDRESS) \
            .method("getPRep") \
            .params({"address": new_prep.get_address()}) \
            .build()
        response = self.process_call(call, self.icon_service)
        self.assertEqual(hex(PRepStatus.UNREGISTERED.value), response['status'], response)

    def test_070_step_price(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'step price network proposal'
        step_price = int(self.get_step_price(), 0) * 120 // 100
        value = {"value": hex(step_price)}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.STEP_PRICE, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('StepPriceChanged(int)', event_log['indexed'][0], event_log)
        self.assertEqual(hex(step_price), event_log['indexed'][1], event_log)
        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # get stePrice
        response = self.get_step_price()
        self.assertEqual(hex(step_price), response, response)

    def test_080_irep(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        irep_current = int(self.get_irep(), 16)

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'irep network proposal'
        irep = irep_current + irep_current // 10
        value = {"value": hex(irep)}
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.IREP, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']
        self.assertEqual(1, response['status'], response)

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event log
        event_log = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log['scoreAddress'], event_log)
        self.assertEqual('IRepChanged(int)', event_log['indexed'][0], event_log)
        self.assertEqual(hex(irep), event_log['indexed'][1], event_log)
        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # get irep
        response = self.get_irep()
        self.assertEqual(hex(irep), response, response)

    def test_090_step_costs(self):
        # go to next P-Rep term for main P-Rep election
        self._make_blocks_to_next_term()

        step_costs_current = self.get_step_costs()

        # register proposal
        proposer = self._test1
        title = "test title"
        desc = 'step costs network proposal'

        contract_call_current = int(step_costs_current[STEP_TYPE_CONTRACT_CALL], 16)
        contract_call = contract_call_current * 2
        contract_create_current = int(step_costs_current[STEP_TYPE_CONTRACT_CREATE], 16)
        contract_create = contract_create_current * 2
        value = {
            STEP_TYPE_CONTRACT_CALL: hex(contract_call),
            STEP_TYPE_CONTRACT_CREATE: hex(contract_create)
        }
        tx = self._create_register_proposal_tx(proposer, title, desc, NetworkProposalType.STEP_COSTS, value)
        response = self.process_transaction(tx, self.icon_service)
        np_id = response['txHash']
        self.assertEqual(1, response['status'], response)

        # vote - agree (15, 69%)
        tx_list = [self._create_vote_proposal_tx(self._test1, np_id, NetworkProposalVote.AGREE)]
        for prep in self._wallet_array[0:14]:
            tx_list.append(self._create_vote_proposal_tx(prep, np_id, NetworkProposalVote.AGREE))
        response = self.process_transaction_bulk(tx_list, self.icon_service)
        for i, resp in enumerate(response):
            self.assertTrue('status' in resp, f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
            self.assertEqual(1, resp['status'], f"{i}:\nTX:\n{tx_list[i].signed_transaction_dict}\nTX_RESULT:\n{resp}")
        # check event logs
        event_log0 = response[-1]['eventLogs'][-2]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log0['scoreAddress'], event_log0)
        self.assertEqual('StepCostChanged(str,int)', event_log0['indexed'][0], event_log0)
        self.assertEqual(STEP_TYPE_CONTRACT_CALL, event_log0['indexed'][1], event_log0)

        event_log1 = response[-1]['eventLogs'][-1]
        self.assertEqual(GOVERNANCE_ADDRESS, event_log1['scoreAddress'], event_log1)
        self.assertEqual('StepCostChanged(str,int)', event_log1['indexed'][0], event_log1)
        self.assertEqual(STEP_TYPE_CONTRACT_CREATE, event_log1['indexed'][1], event_log1)

        # check proposal status
        response = self.get_network_proposal(np_id)
        self.assertEqual(hex(NetworkProposalStatus.APPROVED), response['status'], response)

        # get step costs
        response = self.get_step_costs()
        step_costs = copy.deepcopy(step_costs_current)
        step_costs[STEP_TYPE_CONTRACT_CALL] = hex(contract_call)
        step_costs[STEP_TYPE_CONTRACT_CREATE] = hex(contract_create)
        self.assertEqual(response, step_costs)
