# Copyright 2019 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from os import path
from time import sleep

from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet


def print_response(header, msg):
    print(f'{header}: {json.dumps(msg, indent=4)}')


class TxHandler:
    ZERO_ADDRESS = "cx0000000000000000000000000000000000000000"

    def __init__(self, service):
        self._icon_service = service

    def _deploy(self, owner, to, content, params, limit):
        transaction = DeployTransactionBuilder() \
            .from_(owner.get_address()) \
            .to(to) \
            .step_limit(limit) \
            .version(3) \
            .nid(3) \
            .content_type("application/zip") \
            .content(content) \
            .params(params) \
            .build()
        return self._icon_service.send_transaction(SignedTransaction(transaction, owner))

    def install(self, owner, content, params=None, limit=0x50000000):
        return self._deploy(owner, self.ZERO_ADDRESS, content, params, limit)

    def update(self, owner, to, content, params=None, limit=0x70000000):
        return self._deploy(owner, to, content, params, limit)

    def invoke(self, owner, to, method, params, limit=0x10000000):
        transaction = CallTransactionBuilder() \
            .from_(owner.get_address()) \
            .to(to) \
            .step_limit(limit) \
            .nid(3) \
            .method(method) \
            .params(params) \
            .build()
        return self._icon_service.send_transaction(SignedTransaction(transaction, owner))

    def get_tx_result(self, tx_hash):
        while True:
            try:
                tx_result = self._icon_service.get_transaction_result(tx_hash)
                return tx_result
            except JSONRPCException as e:
                print(e.message)
                sleep(2)


class Governance:
    ADDRESS = "cx0000000000000000000000000000000000000001"

    def __init__(self, service, owner):
        self._icon_service = service
        self._owner = owner

    def _call(self, method, params=None):
        call = CallBuilder() \
            .from_(self._owner.get_address()) \
            .to(self.ADDRESS) \
            .method(method) \
            .params(params) \
            .build()
        return self._icon_service.call(call)

    def get_version(self):
        return self._call("getVersion")

    def get_revision(self):
        return self._call("getRevision")

    def get_service_config(self):
        return self._call("getServiceConfig")

    def get_score_status(self, address):
        params = {
            "address": address
        }
        return self._call("getScoreStatus", params)

    def print_info(self):
        print('[Governance]')
        print_response('Version', self.get_version())
        print_response('Revision', self.get_revision())

    def check_if_audit_enabled(self):
        service_config = self.get_service_config()
        if service_config['AUDIT'] == '0x1':
            return True
        else:
            return False

    def send_accept_score(self, handler: TxHandler, tx_hash):
        params = {
            "txHash": tx_hash
        }
        return handler.invoke(self._owner, self.ADDRESS, "acceptScore", params)


def get_token_content():
    token_score_path = path.join("./score", "sampleToken.zip")
    return gen_deploy_data_content(token_score_path)


def main():
    icon_service = IconService(HTTPProvider("http://localhost:9000/api/v3"))
    owner_wallet = KeyWallet.load("./keystore_test1", "test1_Account")
    print("owner address: ", owner_wallet.get_address())

    gov = Governance(icon_service, owner_wallet)
    gov.print_info()
    audit = gov.check_if_audit_enabled()
    if audit:
        print('Audit: enabled')

    tx_handler = TxHandler(icon_service)
    score_address = None

    for case in ['Install', 'Update']:
        print(f'[{case}]')
        content = get_token_content()
        if case == 'Install':
            params = {
                "_initialSupply": "0x3e8",
                "_decimals": "0x12"
            }
            tx_hash = tx_handler.install(owner_wallet,
                                         content,
                                         params)
        else:
            tx_hash = tx_handler.update(owner_wallet,
                                        score_address,
                                        content)
        print("deploy txHash:", tx_hash)
        tx_result = tx_handler.get_tx_result(tx_hash)
        if tx_result["status"] != 0x1:
            raise Exception('Failed to deploy tx')

        score_address = tx_result["scoreAddress"]
        print("scoreAddress:", score_address)
        score_status = gov.get_score_status(score_address)
        print_response('Status', score_status)

        if audit:
            hash2 = gov.send_accept_score(tx_handler, tx_hash)
            print("accept txHash:", hash2)
            tx_result = tx_handler.get_tx_result(hash2)
            if tx_result["status"] != 0x1:
                raise Exception('Failed to accept tx')
            score_status = gov.get_score_status(score_address)
            print_response('Status after Audit', score_status)


if __name__ == "__main__":
    main()
