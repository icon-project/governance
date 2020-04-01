# import os
#
# from iconsdk.builder.call_builder import CallBuilder
# from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
# from iconsdk.icon_service import IconService
# from iconsdk.libs.in_memory_zip import gen_deploy_data_content
# from iconsdk.providers.http_provider import HTTPProvider
# from iconsdk.signed_transaction import SignedTransaction
# from iconservice.icon_constant import Revision
# from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS
#
# from governance.tests.test_integration_test_network_proposal import GOVERNANCE_ADDRESS, SCORE_PROJECT
#
# DIR_PATH = os.path.abspath(os.path.dirname(__file__))
#
#
# class TestNetworkProposal(IconIntegrateTestBase):IconIntegrateTestBase
#     TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
#     INIT_GOVERNANCE = os.path.abspath(os.path.join(DIR_PATH, 'data/governance_0_0_6.zip'))
#
#     def _get_block_height(self) -> int:
#         block_height: int = 0
#         if self.icon_service:
#             block = self.icon_service.get_block("latest")
#             block_height = block['height']
#         return block_height
#
#     def _reset_block_height(self, need_blocks):
#         iiss_info = self._get_iiss_info()
#
#         next_term = int(iiss_info.get('nextPRepTerm', '0x0'), 16)
#         if next_term == 0:
#             next_term = int(iiss_info.get('nextCalculation', '0x0'), 16)
#         current_block = self._get_block_height()
#
#         if (next_term - current_block) < need_blocks + 1:
#             self._make_blocks(next_term)
#
#     def _make_blocks(self, to: int):
#         block_height = self._get_block_height()
#
#         while to > block_height:
#             self.process_confirm_block_tx(self.icon_service)
#             block_height += 1
#
#     def _make_blocks_to_next_term(self) -> int:
#         iiss_info = self._get_iiss_info()
#         next_term = int(iiss_info.get('nextPRepTerm', 0), 16)
#         if next_term == 0:
#             next_term = int(iiss_info.get('nextCalculation', 0), 16)
#
#         self._make_blocks(to=next_term)
#
#         self.assertEqual(next_term, self._get_block_height())
#         return next_term
#
#     def _get_iiss_info(self) -> dict:
#         call = CallBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(SCORE_INSTALL_ADDRESS) \
#             .method("getIISSInfo") \
#             .build()
#         response = self.process_call(call, self.icon_service)
#         return response
#
#     def _update_governance_score(self, content: str = SCORE_PROJECT) -> dict:
#         tx_result = self._deploy_score(GOVERNANCE_ADDRESS, content)
#         return tx_result
#
#     def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, content: str = SCORE_PROJECT) -> dict:
#         # Generates an instance of transaction for deploying SCORE.
#         transaction = DeployTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(to) \
#             .step_limit(100_000_000_000) \
#             .nid(3) \
#             .nonce(100) \
#             .content_type("application/zip") \
#             .content(gen_deploy_data_content(content)) \
#             .build()
#
#         # Returns the signed transaction object having a signature
#         signed_transaction = SignedTransaction(transaction, self._test1)
#
#         # process the transaction in local
#         tx_result = self.process_transaction(signed_transaction, self.icon_service)
#
#         self.assertTrue('status' in tx_result, tx_result)
#         self.assertEqual(1, tx_result['status'], tx_result)
#         self.assertTrue('scoreAddress' in tx_result, tx_result)
#
#         return tx_result
#
#     def _set_revision(self, code: int, name: str):
#         transaction = CallTransactionBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(GOVERNANCE_ADDRESS) \
#             .step_limit(10_000_000) \
#             .nid(3) \
#             .nonce(100) \
#             .method("setRevision") \
#             .params({"code": code, "name": name}) \
#             .build()
#
#         # Returns the signed transaction object having a signature
#         signed_transaction = SignedTransaction(transaction, self._test1)
#
#         # process the transaction in local
#         tx_result = self.process_transaction(signed_transaction, self.icon_service)
#
#         return tx_result
#
#     def get_revision(self):
#         call = CallBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(GOVERNANCE_ADDRESS) \
#             .method("getRevision") \
#             .build()
#         return self.process_call(call, self.icon_service)
#
#     def get_network_proposal(self, id_: str):
#         call = CallBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(GOVERNANCE_ADDRESS) \
#             .method("getProposal") \
#             .params({"id": id_}) \
#             .build()
#         return self.process_call(call, self.icon_service)
#
#     def get_step_price(self):
#         call = CallBuilder() \
#             .from_(self._test1.get_address()) \
#             .to(GOVERNANCE_ADDRESS) \
#             .method("getStepPrice") \
#             .build()
#         return self.process_call(call, self.icon_service)
#
#     def setUp(self):
#         super().setUp(block_confirm_interval=1, network_only=True)
#         # super().setUp()
#
#         self.icon_service = None
#         # if you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
#         self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))
#
#     def test_001_init_integration_test(self):
#         response = self.get_revision()
#         if isinstance(response['code'], str):
#             print("if")
#             code = int(response['code'], 16)
#         else:
#             print("else")
#             code = 0
#
#         if code < Revision.DECENTRALIZATION.value:
#             # deploy initial governance SCORE
#             self._update_governance_score(self.INIT_GOVERNANCE)
#
#             # enable IISS
#             self._set_revision(Revision.IISS.value, "enable IISS")
#
#             # enable decentralization
#             response = self._set_revision(Revision.DECENTRALIZATION.value, "enable decentralization")
#             self.assertTrue('status' in response, response)
#             self.assertEqual(1, response['status'], response)
