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


if __name__ == '__main__':
    unittest.main()
