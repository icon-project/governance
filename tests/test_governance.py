# Copyright 2021 ICON Foundation
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

import unittest

from governance.governance import *

STEP_COSTS_v0 = {
    STEP_TYPE_DEFAULT: 100_000,
    STEP_TYPE_INPUT: 200,
    STEP_TYPE_CONTRACT_CALL: 25_000,
    STEP_TYPE_CONTRACT_CREATE: 1_000_000_000,
    STEP_TYPE_CONTRACT_UPDATE: 1_600_000_000,
    STEP_TYPE_CONTRACT_DESTRUCT: -70_000,
    STEP_TYPE_CONTRACT_SET: 30_000,
    STEP_TYPE_GET: 0,
    STEP_TYPE_SET: 320,
    STEP_TYPE_REPLACE: 80,
    STEP_TYPE_DELETE: -240,
    STEP_TYPE_EVENT_LOG: 100,
    STEP_TYPE_API_CALL: 10_000
}

STEP_COSTS_v1 = {
    STEP_TYPE_SCHEMA: 1,
    # old types
    STEP_TYPE_DEFAULT: 100_000,
    STEP_TYPE_INPUT: 200,
    STEP_TYPE_CONTRACT_CALL: 25_000,
    STEP_TYPE_CONTRACT_CREATE: 1_000_000_000,
    STEP_TYPE_CONTRACT_UPDATE: 1_000_000_000,
    STEP_TYPE_CONTRACT_SET: 15_000,
    STEP_TYPE_GET: 80,
    STEP_TYPE_SET: 320,
    STEP_TYPE_DELETE: -240,
    STEP_TYPE_API_CALL: 10_000,
    # new types
    STEP_TYPE_GET_BASE: 3_000,
    STEP_TYPE_SET_BASE: 10_000,
    STEP_TYPE_DELETE_BASE: 200,
    STEP_TYPE_LOG_BASE: 5_000,
    STEP_TYPE_LOG: 100,
    # remove
    STEP_TYPE_CONTRACT_DESTRUCT: 0,
    STEP_TYPE_REPLACE: 0,
    STEP_TYPE_EVENT_LOG: 0
}

TEST_ALLOCATION = {
    "iprep": 0x17,
    "icps": 0x18,
    "irelay": 0x1a,
    "ivoter":  0x1b
}


class TestGovernance(unittest.TestCase):

    def test_validate_step_costs_proposal(self):
        costs_v0 = {}
        for k, v in STEP_COSTS_v0.items():
            costs_v0[k] = hex(v)
        value0 = {'costs': costs_v0}
        self.assertTrue(Governance._validate_step_costs_proposal(value0))

        costs_v1 = {}
        for k, v in STEP_COSTS_v1.items():
            costs_v1[k] = hex(v)
        value1 = {'costs': costs_v1}
        self.assertTrue(Governance._validate_step_costs_proposal(value1))

        costs_v1['extra'] = hex(1000)
        value2 = {'costs': costs_v1}
        self.assertFalse(Governance._validate_step_costs_proposal(value2))

        del costs_v1['extra']
        costs_v1[STEP_TYPE_GET] = "cx0"
        value3 = {'costs': costs_v1}
        self.assertFalse(Governance._validate_step_costs_proposal(value3))

    def test_validate_reward_fund_allocation_proposal(self):
        alloc = TEST_ALLOCATION
        funds = {}
        for k, v in alloc.items():
            funds[k] = hex(v)
        value = {'rewardFunds': funds}
        self.assertTrue(Governance._validate_reward_fund_allocation_proposal(value))

        funds['iextra'] = hex(1)
        value1 = {'rewardFunds': funds}
        self.assertFalse(Governance._validate_reward_fund_allocation_proposal(value1))

        del funds['iextra']
        funds['ivoter'] = hex(alloc['ivoter'] + 1)
        value2 = {'rewardFunds': funds}
        self.assertFalse(Governance._validate_reward_fund_allocation_proposal(value2))

        alloc1 = alloc.copy()
        alloc1['ivoter'] += alloc1['icps']
        del alloc1["icps"]
        funds1 = {}
        for k, v in alloc1.items():
            funds1[k] = hex(v)
        value3 = {'rewardFunds': funds1}
        self.assertFalse(Governance._validate_reward_fund_allocation_proposal(value3))

    def test_set_reward_fund_allocation(self):
        class TestGov(Governance):
            def __init__(self):
                self.exp = []
                for v in TEST_ALLOCATION.values():
                    self.exp.append(v)

            def set_reward_fund_allocation(self, iprep: int, icps: int, irelay: int, ivoter: int):
                got = [iprep, icps, irelay, ivoter]
                assert self.exp == got

            def RewardFundAllocationChanged(self, iprep: int, icps: int, irelay: int, ivoter: int):
                got = [iprep, icps, irelay, ivoter]
                assert self.exp == got

        funds = {}
        for k, v in TEST_ALLOCATION.items():
            funds[k] = hex(v)
        gov = TestGov()
        gov._set_reward_fund_allocation(funds)


if __name__ == '__main__':
    unittest.main()
